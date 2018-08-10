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
#include <NFHTTP/Client.h>

#include <sys/stat.h>

#include "CachingClient.h"
#include "ClientCpprestsdk.h"
#include "ClientCurl.h"
#include "ClientModifierImplementation.h"
#include "ClientMultiRequestImplementation.h"
#include "ClientNSURLSession.h"

namespace nativeformat {
namespace http {

static void doNotModifyRequestsFunction(
    std::function<void(const std::shared_ptr<Request> &request)> callback,
    const std::shared_ptr<Request> &request) {
  callback(request);
}

static void doNotModifyResponsesFunction(
    std::function<void(const std::shared_ptr<Response> &response, bool retry)> callback,
    const std::shared_ptr<Response> &response) {
  callback(response, false);
}

const REQUEST_MODIFIER_FUNCTION DO_NOT_MODIFY_REQUESTS_FUNCTION = &doNotModifyRequestsFunction;
const RESPONSE_MODIFIER_FUNCTION DO_NOT_MODIFY_RESPONSES_FUNCTION = &doNotModifyResponsesFunction;

Client::~Client() {}

const std::shared_ptr<Response> Client::performRequestSynchronously(
    const std::shared_ptr<Request> &request) {
  std::mutex mutex;
  std::condition_variable cv;
  std::atomic<bool> response_ready(false);
  std::shared_ptr<Response> output_response = nullptr;
  performRequest(request, [&](const std::shared_ptr<Response> &response) {
    {
      std::lock_guard<std::mutex> lock(mutex);
      output_response = response;
      response_ready = true;
    }
    cv.notify_one();
  });
  std::unique_lock<std::mutex> lock(mutex);
  while (!response_ready) {
    cv.wait(lock);
  }
  return output_response;
}

void Client::pinResponse(const std::shared_ptr<Response> &response,
                         const std::string &pin_identifier) {}

void Client::unpinResponse(const std::shared_ptr<Response> &response,
                           const std::string &pin_identifier) {}

void Client::removePinnedResponseForIdentifier(const std::string &pin_identifier) {}

void Client::pinnedResponsesForIdentifier(
    const std::string &pin_identifier,
    std::function<void(const std::vector<std::shared_ptr<Response>> &)> callback) {}

void Client::pinningIdentifiers(
    std::function<void(const std::vector<std::string> &identifiers)> callback) {}

std::shared_ptr<Client> createNativeClient(const std::string &cache_location,
                                           const std::string &user_agent,
                                           REQUEST_MODIFIER_FUNCTION request_modifier_function,
                                           RESPONSE_MODIFIER_FUNCTION response_modifier_function) {
#if USE_CURL
  return createCurlClient();
#elif USE_CPPRESTSDK
  return createCpprestsdkClient();
#elif __APPLE__
  return createNSURLSessionClient();
#else
  return createCurlClient();
#endif
}

std::shared_ptr<Client> createCachingClient(const std::string &cache_location,
                                            const std::string &user_agent,
                                            REQUEST_MODIFIER_FUNCTION request_modifier_function,
                                            RESPONSE_MODIFIER_FUNCTION response_modifier_function) {
  auto native_client = createNativeClient(
      cache_location, user_agent, request_modifier_function, response_modifier_function);
  // TODO: Make caching client work
  // auto caching_client = std::make_shared<CachingClient>(native_client,
  // cache_location, user_agent);  caching_client->initialise();  return
  // caching_client;
  return native_client;
}

std::shared_ptr<Client> createMultiRequestClient(
    const std::string &cache_location,
    const std::string &user_agent,
    REQUEST_MODIFIER_FUNCTION request_modifier_function,
    RESPONSE_MODIFIER_FUNCTION response_modifier_function) {
  auto caching_client = createCachingClient(
      cache_location, user_agent, request_modifier_function, response_modifier_function);
  return std::make_shared<ClientMultiRequestImplementation>(caching_client);
}

std::shared_ptr<Client> createModifierClient(
    const std::string &cache_location,
    const std::string &user_agent,
    REQUEST_MODIFIER_FUNCTION request_modifier_function,
    RESPONSE_MODIFIER_FUNCTION response_modifier_function) {
  auto multi_request_client = createMultiRequestClient(
      cache_location, user_agent, request_modifier_function, response_modifier_function);
  return std::make_shared<ClientModifierImplementation>(
      request_modifier_function, response_modifier_function, multi_request_client);
}

std::shared_ptr<Client> createClient(const std::string &cache_location,
                                     const std::string &user_agent,
                                     REQUEST_MODIFIER_FUNCTION request_modifier_function,
                                     RESPONSE_MODIFIER_FUNCTION response_modifier_function) {
  return createModifierClient(
      cache_location, user_agent, request_modifier_function, response_modifier_function);
}

}  // namespace http
}  // namespace nativeformat
