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
#include <NFHTTP/ResponseImplementation.h>

#include "RequestImplementation.h"

#include <cstdlib>

#include <nlohmann/json.hpp>

namespace nativeformat {
namespace http {

static const std::string status_code_key("status_code");
static const std::string request_key("request");
static const std::string headers_key("headers");
static const std::string maxage_key("max-age");
static const std::string s_maxage_key("s-maxage");

ResponseImplementation::ResponseImplementation(
    const std::shared_ptr<Request> &request, const unsigned char *data,
    size_t data_length, StatusCode status_code, bool cancelled)
    : _request(request),
      _data(data_length == 0 ? nullptr : (unsigned char *)malloc(data_length)),
      _data_length(data_length), _status_code(status_code),
      _cancelled(cancelled) {
  if (data_length > 0) {
    memcpy(_data, data, data_length);
  }
}

ResponseImplementation::ResponseImplementation(
    const std::string &serialised, const unsigned char *data,
    size_t data_length, const std::shared_ptr<Response> &response)
    : _data(data_length == 0 ? nullptr : (unsigned char *)malloc(data_length)),
      _data_length(data_length), _status_code(StatusCodeInvalid),
      _cancelled(false) {
  nlohmann::json j = nlohmann::json::parse(serialised);
  _request = std::make_shared<RequestImplementation>(
      j[request_key].get<std::string>());
  _status_code = j[status_code_key];
  auto o = j[headers_key];
  for (nlohmann::json::iterator it = o.begin(); it != o.end(); ++it) {
    _headers[it.key()] = it.value();
  }
  if (response) {
    for (const auto &header_pair : response->headerMap()) {
      _headers[header_pair.first] = header_pair.second;
    }
  }
}

ResponseImplementation::~ResponseImplementation() {
  if (_data != nullptr) {
    free(_data);
  }
}

const std::shared_ptr<Request> ResponseImplementation::request() const {
  return _request;
}

const unsigned char *ResponseImplementation::data(size_t &data_length) const {
  data_length = _data_length;
  return _data;
}

StatusCode ResponseImplementation::statusCode() const { return _status_code; }

bool ResponseImplementation::cancelled() const { return _cancelled; }

std::string ResponseImplementation::serialise() const {
  nlohmann::json j = {{status_code_key, statusCode()},
                      {request_key, _request->serialise()}};
  return j.dump();
}

std::string ResponseImplementation::
operator[](const std::string &header_name) const {
  return _headers.at(header_name);
}

std::string &ResponseImplementation::
operator[](const std::string &header_name) {
  return _headers[header_name];
}

std::unordered_map<std::string, std::string> &
ResponseImplementation::headerMap() {
  return _headers;
}

std::unordered_map<std::string, std::string>
ResponseImplementation::headerMap() const {
  return _headers;
}

Response::CacheControl ResponseImplementation::cacheControl() const {
  const auto &cache_control_iterator = _headers.find("Cache-Control");
  if (cache_control_iterator == _headers.end()) {
    return {false, false, false, false, false, false, false, 0, 0};
  }

  std::unordered_map<std::string, std::string> control_directives;
  std::istringstream ss((*cache_control_iterator).second);
  std::string token;
  while (std::getline(ss, token, ',')) {
    token.erase(remove_if(token.begin(), token.end(), isspace), token.end());
    const auto equal_index = token.find("=");
    if (equal_index == std::string::npos || equal_index == token.length() - 1) {
      control_directives[token] = "";
    } else {
      control_directives[token.substr(0, equal_index)] =
          token.substr(equal_index + 1);
    }
  }

  int max_age = 0;
  if (control_directives.find(maxage_key) != control_directives.end()) {
    max_age = std::stoi(control_directives[maxage_key]);
  }
  int s_maxage = 0;
  if (control_directives.find(s_maxage_key) != control_directives.end()) {
    s_maxage = std::stoi(control_directives[s_maxage_key]);
  }
  return {
      control_directives.find("must-revalidate") != control_directives.end(),
      control_directives.find("no-cache") != control_directives.end(),
      control_directives.find("no-store") != control_directives.end(),
      control_directives.find("no-transform") != control_directives.end(),
      control_directives.find("public") != control_directives.end(),
      control_directives.find("private") != control_directives.end(),
      control_directives.find("proxy-revalidate") != control_directives.end(),
      max_age,
      s_maxage};
}

std::unordered_map<std::string, std::string>
ResponseImplementation::metadata() const {
  return _metadata;
}

void ResponseImplementation::setMetadata(const std::string &key,
                                         const std::string &value) {
  _metadata[key] = value;
}

} // namespace http
} // namespace nativeformat
