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

#include <NFHTTP/Request.h>
#include <NFHTTP/RequestToken.h>
#include <NFHTTP/Response.h>

#include <functional>
#include <memory>
#include <mutex>
#include <string>
#include <vector>

namespace nativeformat {
namespace http {

typedef std::function<void(std::function<void(const std::shared_ptr<Request> &request)> callback,
                           const std::shared_ptr<Request> &request)>
    REQUEST_MODIFIER_FUNCTION;
typedef std::function<void(
    std::function<void(const std::shared_ptr<Response> &response, bool retry)> callback,
    const std::shared_ptr<Response> &response)>
    RESPONSE_MODIFIER_FUNCTION;

extern const REQUEST_MODIFIER_FUNCTION DO_NOT_MODIFY_REQUESTS_FUNCTION;
extern const RESPONSE_MODIFIER_FUNCTION DO_NOT_MODIFY_RESPONSES_FUNCTION;

class Client {
 public:
  virtual ~Client();

  virtual std::shared_ptr<RequestToken> performRequest(
      const std::shared_ptr<Request> &request,
      std::function<void(const std::shared_ptr<Response> &)> callback) = 0;
  virtual const std::shared_ptr<Response> performRequestSynchronously(
      const std::shared_ptr<Request> &request);
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
};

extern std::shared_ptr<Client> createClient(
    const std::string &cache_location,
    const std::string &user_agent,
    REQUEST_MODIFIER_FUNCTION request_modifier_function = DO_NOT_MODIFY_REQUESTS_FUNCTION,
    RESPONSE_MODIFIER_FUNCTION response_modifier_function = DO_NOT_MODIFY_RESPONSES_FUNCTION);
extern std::string standardCacheLocation();

}  // namespace http
}  // namespace nativeformat
