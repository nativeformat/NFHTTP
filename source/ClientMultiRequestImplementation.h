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
#pragma once

#include <NFHTTP/Client.h>

#include <memory>
#include <unordered_map>

#include "RequestTokenDelegate.h"

namespace nativeformat {
namespace http {

class ClientMultiRequestImplementation
    : public Client,
      public std::enable_shared_from_this<ClientMultiRequestImplementation>,
      public RequestTokenDelegate {
 public:
  ClientMultiRequestImplementation(std::shared_ptr<Client> &wrapped_client);
  virtual ~ClientMultiRequestImplementation();

  // Client
  std::shared_ptr<RequestToken> performRequest(
      const std::shared_ptr<Request> &request,
      std::function<void(const std::shared_ptr<Response> &)> callback) override;
  void pinResponse(const std::shared_ptr<Response> &response,
                   const std::string &pin_identifier) override;
  void unpinResponse(const std::shared_ptr<Response> &response,
                     const std::string &pin_identifier) override;
  void removePinnedResponseForIdentifier(const std::string &pin_identifier) override;
  void pinnedResponsesForIdentifier(
      const std::string &pin_identifier,
      std::function<void(const std::vector<std::shared_ptr<Response>> &)> callback) override;
  void pinningIdentifiers(
      std::function<void(const std::vector<std::string> &identifiers)> callback) override;

  // RequestTokenDelegate
  void requestTokenDidCancel(const std::shared_ptr<RequestToken> &request_token) override;

 private:
  struct MultiRequest {
    std::function<void(const std::shared_ptr<Response> &)> callback;
    std::weak_ptr<RequestToken> request_token;
  };
  struct MultiRequests {
    std::vector<MultiRequest> multi_requests;
    std::shared_ptr<RequestToken> request_token;
  };

  const std::shared_ptr<Client> _wrapped_client;

  std::unordered_map<std::string, MultiRequests> _requests_in_flight;
  std::mutex _requests_in_flight_mutex;
};

}  // namespace http
}  // namespace nativeformat
