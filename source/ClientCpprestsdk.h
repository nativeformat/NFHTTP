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

#ifdef USE_CPPRESTSDK

#include <NFHTTP/Client.h>
#include <NFHTTP/ResponseImplementation.h>

#include "RequestTokenDelegate.h"
#include "RequestTokenImplementation.h"

#include <cpprest/filestream.h>
#include <cpprest/http_client.h>

#include <thread>

namespace nativeformat {
namespace http {

class ClientCpprestsdk : public Client,
                         public RequestTokenDelegate,
                         public std::enable_shared_from_this<ClientCpprestsdk> {
public:
  ClientCpprestsdk();
  virtual ~ClientCpprestsdk();

  // Client
  std::shared_ptr<RequestToken> performRequest(
      const std::shared_ptr<Request> &request,
      std::function<void(const std::shared_ptr<Response> &)> callback) override;

  // RequestTokenDelegate
  void requestTokenDidCancel(
      const std::shared_ptr<RequestToken> &request_token) override;
};

extern std::shared_ptr<Client> createCpprestsdkClient();

} // namespace http
} // namespace nativeformat

#endif // USE_CPPRESTSDK
