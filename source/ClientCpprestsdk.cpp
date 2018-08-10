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

#include "ClientCpprestsdk.h"

#include <cstring>
#include <memory>

namespace nativeformat {
namespace http {

using namespace utility;           // Common utilities like string conversions
using namespace web;               // Common features like URIs.
using namespace web::http;         // Common HTTP functionality
using namespace web::http::client; // HTTP client features
using namespace concurrency::streams; // Asynchronous streams

// File scope helper functions
static const std::map<std::string, web::http::method> &methodMap();
static const web::http::client::http_client_config &clientConfigForProxy();
static const bool isRedirect(StatusCode code);
static const std::string getRedirectUrl(const http_response &response,
                                        const std::string &request_url);

// ClientCpprestsdk members
ClientCpprestsdk::ClientCpprestsdk() {}
ClientCpprestsdk::~ClientCpprestsdk() {}

std::shared_ptr<RequestToken> ClientCpprestsdk::performRequest(
    const std::shared_ptr<Request> &request,
    std::function<void(const std::shared_ptr<Response> &)> callback) {
  container_buffer<std::string> buf;
  http_headers headers;
  http_request req;
  const std::string base_url = request->url();
  http_client client(conversions::utf8_to_utf16(base_url),
                     clientConfigForProxy());
  std::shared_ptr<ResponseImplementation> r = nullptr;

  for (const auto h : request->headerMap()) {
    headers.add(conversions::utf8_to_utf16(h.first),
                conversions::utf8_to_utf16(h.second));
  }
  req.headers() = headers;
  req.set_method(methodMap().at(request->method()));

  // printf("Starting request to %s...\n", request->url().c_str());
  auto resp = client.request(req).then([=](http_response response) -> void {
    // On request completion, create response and call callback
    StatusCode status = StatusCode(response.status_code());

    // Perform redirect if needed
    if (isRedirect(status)) {
      const std::string new_url = getRedirectUrl(response, request->url());
      std::shared_ptr<Request> new_request =
          createRequest(new_url, request->headerMap());
      this->performRequest(new_request, callback);
      return;
    }
    response.body().read_to_end(buf).wait();
    // printf("Response body:\n%s\n", buf.collection().c_str());
    // printf("Returning response (status = %d)\n", response.status_code());
    const std::string &data = buf.collection();
    std::shared_ptr<ResponseImplementation> r =
        std::make_shared<ResponseImplementation>(
            request, (const unsigned char *)data.c_str(), data.size(), status,
            false);
    callback(r);
  });

  /*
  try {
        resp.wait();
    } catch (web::http::http_exception& e) {
        std::cout << "HTTP EXCEPTION: " << e.what() << " CODE: " <<
  e.error_code() << std::endl; raise(SIGTRAP); } catch (std::exception& e) {
        std::cout << "EXCEPTION: " << e.what() << std::endl;
        raise(SIGTRAP);
    }
  */

  std::string request_hash = request->hash();
  std::shared_ptr<RequestToken> request_token =
      std::make_shared<RequestTokenImplementation>(shared_from_this(),
                                                   request_hash);
  return request_token;
}

void ClientCpprestsdk::requestTokenDidCancel(
    const std::shared_ptr<RequestToken> &request_token) {}

const std::map<std::string, web::http::method> &methodMap() {
  static const std::map<std::string, web::http::method> method_map = {
      {GetMethod, web::http::methods::GET},
      {PostMethod, web::http::methods::POST},
      {PutMethod, web::http::methods::PUT},
      {HeadMethod, web::http::methods::HEAD},
      {DeleteMethod, web::http::methods::DEL},
      {OptionsMethod, web::http::methods::OPTIONS},
      {ConnectMethod, web::http::methods::CONNECT}};
  return method_map;
}

const web::http::client::http_client_config &clientConfigForProxy() {
  static web::http::client::http_client_config client_config;
#ifdef _WIN32
  wchar_t *pValue = nullptr;
  std::unique_ptr<wchar_t, void (*)(wchar_t *)> holder(
      nullptr, [](wchar_t *p) { free(p); });
  size_t len = 0;
  auto err = _wdupenv_s(&pValue, &len, L"http_proxy");
  if (pValue)
    holder.reset(pValue);
  if (!err && pValue && len) {
    std::wstring env_http_proxy_string(pValue, len - 1);
#else
  if (const char *env_http_proxy = std::getenv("http_proxy")) {
    std::string env_http_proxy_string(env_http_proxy);
#endif
    if (env_http_proxy_string == conversions::utf8_to_utf16("auto"))
      client_config.set_proxy(web::web_proxy::use_auto_discovery);
    else
      client_config.set_proxy(web::web_proxy(env_http_proxy_string));
  }

  return client_config;
}

static const bool isRedirect(StatusCode code) {
  if (code >= StatusCodeMovedMultipleChoices &&
      code <= StatusCodeTemporaryRedirect) {
    return true;
  }
  return false;
}

static const std::string getRedirectUrl(const http_response &response,
                                        const std::string &request_url) {
  // Assume if we are here this is definitely a 3xx response code
  // Also assume we're just going to grab the Location header for all 3xx
  static const auto LOCATION_HEADER = U("Location");
  std::string location =
      response.headers().has(LOCATION_HEADER)
          ? conversions::utf16_to_utf8(
                response.headers().find(LOCATION_HEADER)->second)
          : "";
  return !std::strncmp("http", location.c_str(), 4) ? location
                                                    : request_url + location;
}

std::shared_ptr<Client> createCpprestsdkClient() {
  return std::make_shared<ClientCpprestsdk>();
}

} // namespace http
} // namespace nativeformat
