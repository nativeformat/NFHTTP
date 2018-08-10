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
#include "RequestImplementation.h"

#include <nlohmann/json.hpp>

#include "sha256.h"

namespace nativeformat {
namespace http {

static const std::string url_key("url");
static const std::string headers_key("headers");
static const std::string method_key("method");
static const std::string content_length_key("Content-Length");

RequestImplementation::RequestImplementation(
    const std::string &url,
    const std::unordered_map<std::string, std::string> &header_map)
    : _url(url), _headers(header_map), _method(GetMethod), _data(nullptr),
      _data_length(0) {
  _headers[content_length_key] = "0";
}

RequestImplementation::RequestImplementation(const Request &request)
    : _url(request.url()), _headers(request.headerMap()),
      _method(request.method()), _data(nullptr), _data_length(0) {
  size_t data_length = 0;
  const unsigned char *data = request.data(data_length);
  if (data_length > 0) {
    _data = (unsigned char *)malloc(data_length);
    memcpy(_data, data, data_length);
    _data_length = data_length;
  }
}

RequestImplementation::RequestImplementation(const std::string &serialised)
    : _data(nullptr), _data_length(0) {
  nlohmann::json j = nlohmann::json::parse(serialised);
  _url = j[url_key];
  auto o = j[headers_key];
  for (nlohmann::json::iterator it = o.begin(); it != o.end(); ++it) {
    _headers[it.key()] = it.value();
  }
  _method = j[method_key];
}

RequestImplementation::~RequestImplementation() {
  if (_data) {
    free(_data);
  }
}

std::string RequestImplementation::url() const { return _url; }

void RequestImplementation::setUrl(const std::string &url) { _url = url; }

std::string RequestImplementation::
operator[](const std::string &header_name) const {
  return _headers.at(header_name);
}

std::string &RequestImplementation::operator[](const std::string &header_name) {
  return _headers[header_name];
}

std::unordered_map<std::string, std::string> &
RequestImplementation::headerMap() {
  return _headers;
}

std::unordered_map<std::string, std::string>
RequestImplementation::headerMap() const {
  return _headers;
}

std::string RequestImplementation::hash() const {
  // Support "Vary" headers
  std::vector<std::string> excluded_headers;
  const auto &vary_iterator = _headers.find("Vary");
  if (vary_iterator != _headers.end()) {
    std::istringstream ss((*vary_iterator).second);
    std::string token;
    while (std::getline(ss, token, ',')) {
      token.erase(remove_if(token.begin(), token.end(), isspace), token.end());
      excluded_headers.push_back(token);
    }
  }

  std::string amalgamation = url();
  for (const auto &header_pair : _headers) {
    if (std::find(excluded_headers.begin(), excluded_headers.end(),
                  header_pair.first) != excluded_headers.end()) {
      continue;
    }
    amalgamation += header_pair.first + header_pair.second;
  }
  if (_data != nullptr) {
    amalgamation.append((const char *)_data, _data_length);
  }
  return sha256(amalgamation);
}

std::string RequestImplementation::serialise() const {
  nlohmann::json j = {
      {url_key, _url}, {headers_key, _headers}, {method_key, _method}};
  return j.dump();
}

std::string RequestImplementation::method() const { return _method; }

void RequestImplementation::setMethod(const std::string &method) {
  _method = method;
}

const unsigned char *RequestImplementation::data(size_t &data_length) const {
  data_length = _data_length;
  return _data;
}

void RequestImplementation::setData(const unsigned char *data,
                                    size_t data_length) {
  if (_data) {
    free(_data);
    _data = nullptr;
    _data_length = data_length;
  }
  if (data_length > 0) {
    _data = (unsigned char *)malloc(data_length + 1);
    memcpy(_data, data, data_length);
    _data[data_length] = 0;
    _data_length = data_length;
  }
  _headers[content_length_key] = std::to_string(data_length);
}

Request::CacheControl RequestImplementation::cacheControl() const {
  const auto &cache_control_iterator = _headers.find("Cache-Control");
  if (cache_control_iterator == _headers.end()) {
    return {0, 0, 0, false, false, false, false};
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

  return {std::stoi(control_directives["max-age"]),
          std::stoi(control_directives["max-stale"]),
          std::stoi(control_directives["min-fresh"]),
          control_directives.find("no-cache") != control_directives.end(),
          control_directives.find("no-store") != control_directives.end(),
          control_directives.find("no-transform") != control_directives.end(),
          control_directives.find("only-if-cached") !=
              control_directives.end()};
}

} // namespace http
} // namespace nativeformat
