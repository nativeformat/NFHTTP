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
#include "ClientModifierImplementation.h"

#include "RequestTokenImplementation.h"

namespace nativeformat {
namespace http {

ClientModifierImplementation::ClientModifierImplementation(
    REQUEST_MODIFIER_FUNCTION request_modifier_function,
    RESPONSE_MODIFIER_FUNCTION response_modifier_function,
    std::shared_ptr<Client> &wrapped_client)
    : _request_modifier_function(request_modifier_function),
      _response_modifier_function(response_modifier_function),
      _wrapped_client(wrapped_client) {}

ClientModifierImplementation::~ClientModifierImplementation() {}

std::shared_ptr<RequestToken> ClientModifierImplementation::performRequest(
    const std::shared_ptr<Request> &request,
    std::function<void(const std::shared_ptr<Response> &)> callback) {
  auto weak_this = std::weak_ptr<ClientModifierImplementation>(shared_from_this());
  auto request_identifier = request->hash();
  auto request_token = std::make_shared<RequestTokenImplementation>(weak_this, request_identifier);
  _request_modifier_function(
      [weak_this, callback, request_token, request_identifier](
          const std::shared_ptr<Request> &request) {
        if (request_token->cancelled()) {
          return;
        }
        if (auto strong_this = weak_this.lock()) {
          auto new_request_token = strong_this->_wrapped_client->performRequest(
              request,
              [callback, weak_this, request, request_identifier](
                  const std::shared_ptr<Response> &response) {
                if (auto strong_this = weak_this.lock()) {
                  strong_this->_response_modifier_function(
                      [callback, weak_this, request_identifier](
                          const std::shared_ptr<Response> &response, bool retry) {
                        if (retry) {
                          if (auto strong_this = weak_this.lock()) {
                            auto request_token =
                                strong_this->performRequest(response->request(), callback);
                            auto new_request_identifier = request_token->identifier();
                            {
                              std::lock_guard<std::mutex> request_map_lock(
                                  strong_this->_request_map_mutex);
                              strong_this->_request_identifier_map[request_identifier] =
                                  new_request_identifier;
                              strong_this->_request_token_map[new_request_identifier] =
                                  request_token;
                            }
                            return;
                          }
                        }
                        callback(response);
                        if (auto strong_this = weak_this.lock()) {
                          std::lock_guard<std::mutex> request_map_lock(
                              strong_this->_request_map_mutex);
                          strong_this->_request_token_map.erase(
                              strong_this->_request_identifier_map[request_identifier]);
                          strong_this->_request_identifier_map.erase(request_identifier);
                        }
                      },
                      response);
                }
              });
          auto new_request_identifier = new_request_token->identifier();
          {
            std::lock_guard<std::mutex> request_map_lock(strong_this->_request_map_mutex);
            strong_this->_request_identifier_map[request_identifier] = new_request_identifier;
            strong_this->_request_token_map[new_request_identifier] = new_request_token;
          }
        }
      },
      request);
  return request_token;
}

void ClientModifierImplementation::pinResponse(const std::shared_ptr<Response> &response,
                                               const std::string &pin_identifier) {
  return _wrapped_client->pinResponse(response, pin_identifier);
}

void ClientModifierImplementation::unpinResponse(const std::shared_ptr<Response> &response,
                                                 const std::string &pin_identifier) {
  return _wrapped_client->unpinResponse(response, pin_identifier);
}

void ClientModifierImplementation::removePinnedResponseForIdentifier(
    const std::string &pin_identifier) {
  _wrapped_client->removePinnedResponseForIdentifier(pin_identifier);
}

void ClientModifierImplementation::pinnedResponsesForIdentifier(
    const std::string &pin_identifier,
    std::function<void(const std::vector<std::shared_ptr<Response>> &)> callback) {
  _wrapped_client->pinnedResponsesForIdentifier(pin_identifier, callback);
}

void ClientModifierImplementation::pinningIdentifiers(
    std::function<void(const std::vector<std::string> &identifiers)> callback) {
  _wrapped_client->pinningIdentifiers(callback);
}

void ClientModifierImplementation::requestTokenDidCancel(
    const std::shared_ptr<RequestToken> &request_token) {
  std::lock_guard<std::mutex> request_map_lock(_request_map_mutex);
  auto identifier = request_token->identifier();
  auto new_identifier = _request_identifier_map[identifier];
  auto new_request_token = _request_token_map[new_identifier];
  if (auto new_request_token_strong = new_request_token.lock()) {
    new_request_token_strong->cancel();
  }
  _request_identifier_map.erase(identifier);
  _request_token_map.erase(new_identifier);
}

}  // namespace http
}  // namespace nativeformat
