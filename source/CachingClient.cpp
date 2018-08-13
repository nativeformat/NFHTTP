/*
 * Copyright (c) 2017 Spotify AB.
 *
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */
#include "CachingClient.h"

#include <NFHTTP/ResponseImplementation.h>
#include "RequestImplementation.h"

#include <chrono>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <locale>
#include <sstream>
#include <unordered_map>

#include "RequestTokenImplementation.h"

namespace nativeformat {
namespace http {

namespace {
static const std::string CACHED_KEY("cached");
}  // namespace

CachingClient::CachingClient(const std::shared_ptr<Client> &client,
                             const std::string &cache_location)
    : _client(client),
      _cache_location(cache_location.back() == '/' ? cache_location : cache_location + "/") {}

CachingClient::~CachingClient() {
  _shutdown_prune_thread = true;
  _prune_thread.join();
}

void CachingClient::requestTokenDidCancel(const std::shared_ptr<RequestToken> &request_token) {
  if (auto token = _tokens[request_token].lock()) {
    token->cancel();
  }
}

void CachingClient::deleteDatabaseFile(const std::string &header_hash) {
  remove((_cache_location + header_hash).c_str());
}

std::shared_ptr<RequestToken> CachingClient::performRequest(
    const std::shared_ptr<Request> &request,
    std::function<void(const std::shared_ptr<Response> &)> callback) {
  std::shared_ptr<Request> new_request = std::make_shared<RequestImplementation>(*request.get());
  std::string request_hash = new_request->hash();

  std::shared_ptr<RequestToken> request_token = nullptr;
  if (!shouldCacheRequest(new_request)) {
    request_token = _client->performRequest(new_request, callback);
  } else {
    request_token = std::make_shared<RequestTokenImplementation>(shared_from_this(), request_hash);
    _database->fetchItemForRequest(
        request_hash,
        [request_token, callback, new_request, this](CachingDatabase::ErrorCode code,
                                                     const CacheItem &item) {
          if (request_token->cancelled()) {
            std::shared_ptr<Response> cancelled_response = std::make_shared<ResponseImplementation>(
                new_request, nullptr, 0, StatusCodeInvalid, true);
            callback(cancelled_response);
            return;
          }
          // Possible problem here when cancel is called after this, we need to
          // do this atomically

          auto wrapped_callback = [callback, item, this, request_token](
                                      const std::shared_ptr<Response> &response) {
            Response::CacheControl cache_control = response->cacheControl();
            if (cache_control.no_store || cache_control.no_cache) {
              callback(response);
            } else {
              switch (response->statusCode()) {
                case StatusCodeOK:
                case StatusCodeCreated:
                case StatusCodeAccepted:
                case StatusCodeNonAuthoritiveInformation:
                case StatusCodeNoContent:
                case StatusCodeResetContent:
                case StatusCodePartialContent:
                  _database->storeResponse(
                      response,
                      [callback, item, this](CachingDatabase::ErrorCode code,
                                             const std::shared_ptr<Response> &response) {
                        // Write the cached file back to disk
                        std::string filename =
                            item.valid ? item.payload_filename : response->request()->hash();
                        FILE *cache_file = fopen((_cache_location + filename).c_str(), "w");
                        size_t data_length = 0;
                        const unsigned char *data = response->data(data_length);
                        fwrite(data, data_length, 1, cache_file);
                        fclose(cache_file);
                        callback(response);
                      });
                  break;
                case StatusCodeNotModified:
                  _database->storeResponse(responseFromCacheItem(item, response),
                                           [callback](CachingDatabase::ErrorCode code,
                                                      const std::shared_ptr<Response> &response) {
                                             callback(response);
                                           });
                  break;
                default:
                  callback(response);
                  break;
              }
            }
            _tokens.erase(request_token);
          };

          // Should we only contact the cache?
          if (item.valid) {
            Request::CacheControl cache_control = new_request->cacheControl();
            std::shared_ptr<Response> response = responseFromCacheItem(item);
            if (cache_control.only_if_cached) {
              callback(response);
              return;
            }

            // Check cache validity
            Response::CacheControl response_cache_control = response->cacheControl();
            std::time_t result = std::time(nullptr);
            bool expired = difftime(result, item.expiry_time) > cache_control.max_stale;
            if (expired || response_cache_control.must_revalidate) {
              // If it has expired, lets add some extra caching headers
              if (item.etag.length() > 0) {
                (*new_request)["If-None-Match"] = item.etag;
              } else if (item.last_modified != 0) {
                auto tm = *std::localtime(&item.last_modified);
                std::ostringstream output_string_stream;
                output_string_stream << std::put_time(&tm, "%d-%m-%Y %H-%M-%S");
                (*new_request)["If-Modified-Since"] = output_string_stream.str();
              }
              _tokens[request_token] = _client->performRequest(new_request, wrapped_callback);
              return;
            } else {
              callback(response);
              _tokens.erase(request_token);
              return;
            }
          }

          _tokens[request_token] = _client->performRequest(new_request, wrapped_callback);
        });
  }
  return request_token;
}

void CachingClient::pinResponse(const std::shared_ptr<Response> &response,
                                const std::string &pin_identifier) {
  _database->fetchItemForRequest(
      response->request()->hash(),
      [this, pin_identifier](CachingDatabase::ErrorCode error_code, const CacheItem &item) {
        _database->pinItem(item, pin_identifier);
      });
}

void CachingClient::unpinResponse(const std::shared_ptr<Response> &response,
                                  const std::string &pin_identifier) {
  _database->fetchItemForRequest(
      response->request()->hash(),
      [this, pin_identifier](CachingDatabase::ErrorCode error_code, const CacheItem &item) {
        _database->unpinItem(item, pin_identifier);
      });
}

void CachingClient::removePinnedResponseForIdentifier(const std::string &pin_identifier) {
  _database->removePinnedItemsForIdentifier(pin_identifier);
}

void CachingClient::pinnedResponsesForIdentifier(
    const std::string &pin_identifier,
    std::function<void(const std::vector<std::shared_ptr<Response>> &)> callback) {
  _database->pinnedItemsForIdentifier(pin_identifier,
                                      [callback, this](const std::vector<CacheItem> &items) {
                                        std::vector<std::shared_ptr<Response>> responses;
                                        for (const auto &item : items) {
                                          responses.push_back(responseFromCacheItem(item));
                                        }
                                        callback(responses);
                                      });
}

void CachingClient::pinningIdentifiers(
    std::function<void(const std::vector<std::string> &identifiers)> callback) {
  _database->pinningIdentifiers(callback);
}

void CachingClient::pruneThread(CachingClient *client) {
  int counter = 0;
  while (!client->_shutdown_prune_thread) {
    std::this_thread::sleep_for(std::chrono::milliseconds(1));
    if (counter++ == 50000) {
      client->_database->prune();
      counter = 0;
    }
  }
}

const std::shared_ptr<Response> CachingClient::responseFromCacheItem(
    const CacheItem &item, const std::shared_ptr<Response> &response) const {
  FILE *cache_file = fopen((_cache_location + item.payload_filename).c_str(), "r");
  size_t data_length = 0;
  unsigned char *data = NULL;
  if (cache_file != NULL && item.valid) {
    fseek(cache_file, 0, SEEK_END);
    data_length = ftell(cache_file);
    rewind(cache_file);
    data = (unsigned char *)malloc(data_length);
    fread(data, data_length, 1, cache_file);
    fclose(cache_file);
  }

  const std::shared_ptr<Response> output_response =
      std::make_shared<ResponseImplementation>(item.response, data, data_length, response);
  if (data != NULL) {
    free(data);
  }
  output_response->setMetadata(CACHED_KEY, "1");

  return output_response;
}

bool CachingClient::shouldCacheRequest(const std::shared_ptr<Request> &request) {
  if (request->method() == PostMethod || request->method() == DeleteMethod ||
      request->method() == PutMethod) {
    return false;
  }

  Request::CacheControl cache_control = request->cacheControl();
  if (cache_control.no_cache || cache_control.no_store) {
    return false;
  }

  return true;
}

void CachingClient::initialise() {
  _database = createCachingDatabase(_cache_location, "sqlite", shared_from_this());
  _prune_thread = std::thread(pruneThread, this);
}

}  // namespace http
}  // namespace nativeformat
