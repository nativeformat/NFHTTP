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

#include <memory>
#include <string>
#include <unordered_map>

namespace nativeformat {
namespace http {

extern const std::string GetMethod;
extern const std::string PostMethod;
extern const std::string PutMethod;
extern const std::string HeadMethod;
extern const std::string DeleteMethod;
extern const std::string OptionsMethod;
extern const std::string ConnectMethod;

class Request {
 public:
  typedef struct CacheControl {
    const int max_age;
    const int max_stale;
    const int min_fresh;
    const bool no_cache;
    const bool no_store;
    const bool no_transform;
    const bool only_if_cached;
  } CacheControl;

  virtual std::string url() const = 0;
  virtual void setUrl(const std::string &url) = 0;
  virtual std::string operator[](const std::string &header_name) const = 0;
  virtual std::string &operator[](const std::string &header_name) = 0;
  virtual std::unordered_map<std::string, std::string> &headerMap() = 0;
  virtual std::unordered_map<std::string, std::string> headerMap() const = 0;
  virtual std::string hash() const = 0;
  virtual std::string serialise() const = 0;
  virtual std::string method() const = 0;
  virtual void setMethod(const std::string &method) = 0;
  virtual const unsigned char *data(size_t &data_length) const = 0;
  virtual void setData(const unsigned char *data, size_t data_length) = 0;
  virtual CacheControl cacheControl() const = 0;
};

extern std::shared_ptr<Request> createRequest(
    const std::string &url, const std::unordered_map<std::string, std::string> &header_map);
extern std::shared_ptr<Request> createRequest(const std::shared_ptr<Request> &request);

}  // namespace http
}  // namespace nativeformat
