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
#include "ClientCurl.h"

#include <curl/multi.h>
#include <sstream>
#include <unistd.h>

namespace nativeformat {
namespace http {

namespace {

static void setupCurlGlobalState(bool added_client) {
  static long curl_clients_active = 0;
  static std::mutex curl_clients_active_mutex;
  std::lock_guard<std::mutex> lock(curl_clients_active_mutex);
  long previous_curl_clients_active = curl_clients_active;
  if (added_client) {
    curl_clients_active++;
  } else if (curl_clients_active != 0) {
    curl_clients_active--;
  }
  if (previous_curl_clients_active == 0 && curl_clients_active == 1) {
    curl_global_init(CURL_GLOBAL_ALL);
  } else if (previous_curl_clients_active == 1 && curl_clients_active == 0) {
    curl_global_cleanup();
  }
}

} // namespace

ClientCurl::ClientCurl() : _new_request(false), _is_terminated(false) {
  setupCurlGlobalState(true);
  _curl = curl_multi_init();
  curl_multi_setopt(_curl, CURLMOPT_MAXCONNECTS, MAX_CONNECTIONS);
  _request_thread = std::thread(&ClientCurl::mainClientLoop, this);
}

ClientCurl::~ClientCurl() {
  std::unique_lock<std::mutex> client_lock(_client_mutex);

  // Remove any remaining requests
  std::vector<std::string> hashes;
  for (auto &p : _handles) {
    hashes.push_back(p.first);
    curl_multi_remove_handle(_curl, p.second->handle);
  }
  for (auto h : hashes) {
    requestCleanup(h);
  }

  curl_multi_cleanup(_curl);
  setupCurlGlobalState(false);
  _is_terminated = true;
  client_lock.unlock();

  _new_info_condition.notify_all();
  _request_thread.join();
}

size_t ClientCurl::header_callback(char *data, size_t size, size_t nitems,
                                   void *str) {
  auto headers =
      reinterpret_cast<std::unordered_map<std::string, std::string> *>(str);
  std::string s(data, size * nitems), k, v;
  size_t pos;
  if ((pos = s.find(":")) != std::string::npos) {
    k = s.substr(0, pos);
    v = s.substr(std::min(pos + 2, s.length()));
  }
  if (!k.empty()) {
    (*headers)[k] = v;
  }
  return size * nitems;
}

size_t ClientCurl::write_callback(char *data, size_t size, size_t nitems,
                                  void *str) {
  std::string *string_buffer = static_cast<std::string *>(str);
  if (string_buffer == nullptr) {
    return 0;
  }
  // Perhaps it would be good to have a file-backed option?
  string_buffer->append(data, size * nitems);
  return size * nitems;
}

std::shared_ptr<RequestToken> ClientCurl::performRequest(
    const std::shared_ptr<Request> &request,
    std::function<void(const std::shared_ptr<Response> &)> callback) {
  // Lock client mutex before adding request
  std::unique_lock<std::mutex> client_lock(_client_mutex);

  std::string request_hash = request->hash();

  // Add callback and request to map members
  std::shared_ptr<RequestToken> request_token =
      std::make_shared<RequestTokenImplementation>(shared_from_this(),
                                                   request_hash);

  _handles[request_hash] =
      std::unique_ptr<HandleInfo>(new HandleInfo(request, callback));
  std::unique_ptr<HandleInfo> &handle_info = _handles[request_hash];

  // Add easy handle to multi handle
  curl_multi_add_handle(_curl, handle_info->handle);

  // Wake up request thread if it's waiting
  _new_request = true;
  client_lock.unlock();
  _new_info_condition.notify_one();

  return request_token;
}

void ClientCurl::mainClientLoop() {
  CURLMsg *msg;
  long L = 0;
  int M, Q, active_requests = -1;
  fd_set R, W, E;
  struct timeval T;

  curl_global_init(CURL_GLOBAL_ALL);

  std::unique_lock<std::mutex> client_lock(_client_mutex);
  while (true) {
    // launch any waiting requests
    curl_multi_perform(_curl, &active_requests);

    // read any messages that are ready
    size_t msg_count = 0;
    while ((msg = curl_multi_info_read(_curl, &Q))) {
      msg_count++;
      if (msg->msg == CURLMSG_DONE) {
        std::string *request_hash;
        CURL *e = msg->easy_handle;
        curl_easy_getinfo(msg->easy_handle, CURLINFO_PRIVATE, &request_hash);

        // TODO retry?
        if (msg->data.result == CURLE_OPERATION_TIMEDOUT) {
        }

        // make response to send to callback
        long status_code = 0;
        curl_easy_getinfo(e, CURLINFO_RESPONSE_CODE, &status_code);

        // Look up response data and original request
        HandleInfo *handle_info = _handles[*request_hash].get();
        const std::shared_ptr<Request> request = handle_info->request;
        const unsigned char *data =
            (const unsigned char *)handle_info->response.c_str();
        size_t data_length = handle_info->response.size();

        /*
        printf("Got response for: %s\n", request->url().c_str());
        printf("Response code: %lu\n", status_code);
        printf("Response size: %lu\n", data_length);
        */

        std::shared_ptr<Response> new_response =
            std::make_shared<ResponseImplementation>(
                request, data, data_length, StatusCode(status_code), false);

        auto &response_headers = new_response->headerMap();
        response_headers = std::move(handle_info->response_headers);

        // Save callback before cleanup
        auto cb = handle_info->callback;
        curl_multi_remove_handle(_curl, e);
        requestCleanup(*request_hash);

        if (cb) {
          // Release lock before calling callback
          // In case the callback adds a new request
          client_lock.unlock();
          cb(new_response);
          client_lock.lock();
        }
      } else {
        fprintf(stderr, "E: CURLMsg (%d)\n", msg->msg);
      }
    }

    // If we processed a message since checking the active request count,
    // go back and check it again
    if (msg_count)
      continue;

    if (active_requests) {
      FD_ZERO(&R);
      FD_ZERO(&W);
      FD_ZERO(&E);

      if (curl_multi_fdset(_curl, &R, &W, &E, &M)) {
        fprintf(stderr, "E: curl_multi_fdset\n");
      }

      if (curl_multi_timeout(_curl, &L)) {
        fprintf(stderr, "E: curl_multi_timeout\n");
      }
      if (L == -1)
        L = 100;

      if (M == -1) {
        client_lock.unlock();
        usleep((unsigned long)L);
        client_lock.lock();
      } else {
        T.tv_sec = L / 1000;
        T.tv_usec = (L % 1000) * 1000;

        if (0 > select(M + 1, &R, &W, &E, &T)) {
          fprintf(stderr, "E: select(%i,,,,%li): %i: %s\n", M + 1, L, errno,
                  strerror(errno));
        }
      }
    } else {
      // If there are no active requests, wait on condition variable
      _new_request = false;
      _new_info_condition.wait(
          client_lock, [this]() { return (_new_request || _is_terminated); });

      if (_is_terminated) {
        return;
      }
    }
  }
}

void ClientCurl::requestCleanup(std::string hash) { _handles.erase(hash); }

void ClientCurl::requestTokenDidCancel(
    const std::shared_ptr<RequestToken> &request_token) {}

ClientCurl::HandleInfo::HandleInfo(
    std::shared_ptr<Request> req,
    std::function<void(const std::shared_ptr<Response> &)> cbk)
    : request(req), request_headers(nullptr), callback(cbk) {
  handle = curl_easy_init();
  request_hash = request->hash();
  configureCurlHandle();
}

ClientCurl::HandleInfo::HandleInfo()
    : handle(nullptr), request(nullptr), request_headers(nullptr),
      callback(nullptr) {}

ClientCurl::HandleInfo::~HandleInfo() {
  if (request_headers) {
    curl_slist_free_all(request_headers);
  }
  if (handle) {
    curl_easy_cleanup(handle);
  }
}

void ClientCurl::HandleInfo::configureHeaders() {
  struct curl_slist *headers = NULL;
  for (const auto &header : request->headerMap()) {
    if (header.first == "Range") {
      curl_easy_setopt(handle, CURLOPT_RANGE, header.second.substr(6).c_str());
      continue;
    }
    std::stringstream ss;
    ss << header.first << ": " << header.second;
    headers = curl_slist_append(headers, ss.str().c_str());
  }
  // Stash this since we need to free the slist later
  request_headers = headers;
}

void ClientCurl::HandleInfo::configureCurlHandle() {
  // printf("Requesting %s\n", request->url().c_str());
  curl_easy_setopt(handle, CURLOPT_URL, request->url().c_str());
  curl_easy_setopt(handle, CURLOPT_FOLLOWLOCATION, 1L);
  curl_easy_setopt(handle, CURLOPT_WRITEFUNCTION, write_callback);
  curl_easy_setopt(handle, CURLOPT_WRITEDATA, &response);
  curl_easy_setopt(handle, CURLOPT_HEADERFUNCTION, header_callback);
  curl_easy_setopt(handle, CURLOPT_WRITEHEADER, &response_headers);

  curl_easy_setopt(handle, CURLOPT_TIMEOUT, 30);

#if __APPLE__
  curl_easy_setopt(handle, CURLOPT_SSL_VERIFYPEER, false);
  curl_easy_setopt(handle, CURLOPT_SSL_VERIFYHOST, false);
#endif

  // Stash request hash in a pointer so we can get callback later
  curl_easy_setopt(handle, CURLOPT_PRIVATE, &request_hash);

  // Set method
  if (request->method() == GetMethod) {
    curl_easy_setopt(handle, CURLOPT_HTTPGET, 1);
  } else if (request->method() == PutMethod) {
    curl_easy_setopt(handle, CURLOPT_PUT, 1);
  } else if (request->method() == PostMethod) {
    curl_easy_setopt(handle, CURLOPT_POST, 1);
  } else if (request->method() == HeadMethod) {
    curl_easy_setopt(handle, CURLOPT_HTTPGET, 1);
    curl_easy_setopt(handle, CURLOPT_NOBODY, 1);
  } else {
    curl_easy_setopt(handle, CURLOPT_CUSTOMREQUEST, request->method().c_str());
  }

  // Set data
  size_t data_length;
  const unsigned char *request_data = request->data(data_length);
  if (data_length) {
    curl_easy_setopt(handle, CURLOPT_POSTFIELDSIZE, data_length);
    curl_easy_setopt(handle, CURLOPT_POSTFIELDS, request_data);
  }

  // Set custom headers
  configureHeaders();
  curl_easy_setopt(handle, CURLOPT_HEADEROPT, CURLHEADER_UNIFIED);
  curl_easy_setopt(handle, CURLOPT_HTTPHEADER, request_headers);
}

std::shared_ptr<Client> createCurlClient() {
  return std::make_shared<ClientCurl>();
}

} // namespace http
} // namespace nativeformat
