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
#include <NFHTTP/ResponseImplementation.h>

#include "curl/curl.h"

#include <thread>

#include "RequestTokenDelegate.h"
#include "RequestTokenImplementation.h"

namespace nativeformat {
namespace http {

class ClientCurl : public Client,
                   public RequestTokenDelegate,
                   public std::enable_shared_from_this<ClientCurl> {
  struct HandleInfo {
    CURL *handle;
    const std::shared_ptr<Request> request;
    std::string request_hash;
    std::string response;
    curl_slist *request_headers;
    std::unordered_map<std::string, std::string> response_headers;
    std::function<void(const std::shared_ptr<Response> &)> callback;
    HandleInfo(std::shared_ptr<Request> req,
               std::function<void(const std::shared_ptr<Response> &)> cbk);
    HandleInfo();
    ~HandleInfo();

    void configureHeaders();
    void configureCurlHandle();
  };

public:
  ClientCurl();
  virtual ~ClientCurl();

  static const long MAX_CONNECTIONS = 10;

  // Client
  std::shared_ptr<RequestToken> performRequest(
      const std::shared_ptr<Request> &request,
      std::function<void(const std::shared_ptr<Response> &)> callback) override;

  // RequestTokenDelegate
  void requestTokenDidCancel(
      const std::shared_ptr<RequestToken> &request_token) override;

  // Private members
private:
  // Obtain this lock before modifying any members
  std::mutex _client_mutex;

  CURLM *_curl;
  std::condition_variable _new_info_condition;
  bool _new_request;
  std::atomic<bool> _is_terminated;
  std::thread _request_thread;

  std::unordered_map<std::string, std::unique_ptr<HandleInfo>> _handles;
  std::atomic<long> _request_count;

  void mainClientLoop();
  void requestCleanup(std::string hash);

  // Curl callbacks
public:
  static size_t write_callback(char *data, size_t size, size_t nitems,
                               void *str);
  static size_t header_callback(char *data, size_t size, size_t nitems,
                                void *str);
};

extern std::shared_ptr<Client> createCurlClient();

} // namespace http
} // namespace nativeformat
