/*
 * Copyright (c) 2018 Spotify AB.
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
#include "ClientMultiRequestImplementation.h"

#include "RequestTokenImplementation.h"

#include <algorithm>

namespace nativeformat {
namespace http {

namespace {
static const std::string MULTICAST_KEY("multicasted");
}  // namespace

ClientMultiRequestImplementation::ClientMultiRequestImplementation(
    std::shared_ptr<Client> &wrapped_client)
    : _wrapped_client(wrapped_client) {}

ClientMultiRequestImplementation::~ClientMultiRequestImplementation() {}

std::shared_ptr<RequestToken> ClientMultiRequestImplementation::performRequest(
    const std::shared_ptr<Request> &request,
    std::function<void(const std::shared_ptr<Response> &)> callback) {
  std::lock_guard<std::mutex> lock(_requests_in_flight_mutex);
  auto hash = request->hash();
  auto request_it = _requests_in_flight.find(hash);
  if (request_it == _requests_in_flight.end()) {
    MultiRequests multi_requests;
    std::weak_ptr<ClientMultiRequestImplementation> weak_this = shared_from_this();
    multi_requests.request_token = _wrapped_client->performRequest(
        request, [weak_this](const std::shared_ptr<Response> &response) {
          if (auto strong_this = weak_this.lock()) {
            std::vector<std::function<void(const std::shared_ptr<Response> &)>> callbacks;
            {
              std::lock_guard<std::mutex> lock(strong_this->_requests_in_flight_mutex);
              auto hash = response->request()->hash();
              auto &multi_requests = strong_this->_requests_in_flight[hash];
              response->setMetadata(MULTICAST_KEY,
                                    std::to_string(multi_requests.multi_requests.size() > 1));
              for (const auto &multi_request : multi_requests.multi_requests) {
                callbacks.push_back(multi_request.callback);
              }
              strong_this->_requests_in_flight.erase(hash);
            }
            for (const auto &callback : callbacks) {
              callback(response);
            }
          }
        });
    _requests_in_flight[hash] = multi_requests;
  }
  auto token = std::make_shared<RequestTokenImplementation>(shared_from_this(), hash);
  MultiRequest multi_request = {callback, token};
  _requests_in_flight[hash].multi_requests.push_back(multi_request);
  return token;
}

void ClientMultiRequestImplementation::pinResponse(const std::shared_ptr<Response> &response,
                                                   const std::string &pin_identifier) {
  _wrapped_client->pinResponse(response, pin_identifier);
}

void ClientMultiRequestImplementation::unpinResponse(const std::shared_ptr<Response> &response,
                                                     const std::string &pin_identifier) {
  _wrapped_client->unpinResponse(response, pin_identifier);
}

void ClientMultiRequestImplementation::removePinnedResponseForIdentifier(
    const std::string &pin_identifier) {
  _wrapped_client->removePinnedResponseForIdentifier(pin_identifier);
}

void ClientMultiRequestImplementation::pinnedResponsesForIdentifier(
    const std::string &pin_identifier,
    std::function<void(const std::vector<std::shared_ptr<Response>> &)> callback) {
  _wrapped_client->pinnedResponsesForIdentifier(pin_identifier, callback);
}

void ClientMultiRequestImplementation::pinningIdentifiers(
    std::function<void(const std::vector<std::string> &identifiers)> callback) {
  _wrapped_client->pinningIdentifiers(callback);
}

void ClientMultiRequestImplementation::requestTokenDidCancel(
    const std::shared_ptr<RequestToken> &request_token) {
  std::lock_guard<std::mutex> lock(_requests_in_flight_mutex);
  auto identifier = request_token->identifier();
  auto &multi_requests = _requests_in_flight[identifier];
  auto &multi_requests_vector = multi_requests.multi_requests;
  multi_requests_vector.erase(std::remove_if(multi_requests_vector.begin(),
                                             multi_requests_vector.end(),
                                             [&](MultiRequest &multi_request) {
                                               return multi_request.request_token.lock().get() ==
                                                      request_token.get();
                                             }),
                              multi_requests_vector.end());
  if (multi_requests_vector.empty()) {
    multi_requests.request_token->cancel();
    _requests_in_flight.erase(identifier);
  }
}

}  // namespace http
}  // namespace nativeformat
