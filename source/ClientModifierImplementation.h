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
#pragma once

#include <NFHTTP/Client.h>

#include <memory>
#include <unordered_map>

#include "RequestTokenDelegate.h"

namespace nativeformat {
namespace http {

class ClientModifierImplementation
    : public Client,
      public std::enable_shared_from_this<ClientModifierImplementation>,
      public RequestTokenDelegate {
 public:
  ClientModifierImplementation(REQUEST_MODIFIER_FUNCTION request_modifier_function,
                               RESPONSE_MODIFIER_FUNCTION response_modifier_function,
                               std::shared_ptr<Client> &wrapped_client);
  virtual ~ClientModifierImplementation();

  // Client
  virtual std::shared_ptr<RequestToken> performRequest(
      const std::shared_ptr<Request> &request,
      std::function<void(const std::shared_ptr<Response> &)> callback);
  virtual void pinResponse(const std::shared_ptr<Response> &response,
                           const std::string &pin_identifier);
  virtual void unpinResponse(const std::shared_ptr<Response> &response,
                             const std::string &pin_identifier);
  virtual void removePinnedResponseForIdentifier(const std::string &pin_identifier);
  virtual void pinnedResponsesForIdentifier(
      const std::string &pin_identifier,
      std::function<void(const std::vector<std::shared_ptr<Response>> &)> callback);
  virtual void pinningIdentifiers(
      std::function<void(const std::vector<std::string> &identifiers)> callback);

  // RequestTokenDelegate
  virtual void requestTokenDidCancel(const std::shared_ptr<RequestToken> &request_token);

 private:
  const REQUEST_MODIFIER_FUNCTION _request_modifier_function;
  const RESPONSE_MODIFIER_FUNCTION _response_modifier_function;
  const std::shared_ptr<Client> _wrapped_client;

  std::unordered_map<std::string, std::string> _request_identifier_map;
  std::unordered_map<std::string, std::weak_ptr<RequestToken>> _request_token_map;
  std::mutex _request_map_mutex;
};

}  // namespace http
}  // namespace nativeformat
