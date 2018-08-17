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

namespace nativeformat {
namespace http {

class RequestImplementation : public Request {
 public:
  RequestImplementation(const std::string &url,
                        const std::unordered_map<std::string, std::string> &header_map);
  RequestImplementation(const Request &request);
  RequestImplementation(const std::string &serialised);
  virtual ~RequestImplementation();

  // Request
  std::string url() const override;
  void setUrl(const std::string &url) override;
  std::string operator[](const std::string &header_name) const override;
  std::string &operator[](const std::string &header_name) override;
  std::unordered_map<std::string, std::string> &headerMap() override;
  std::unordered_map<std::string, std::string> headerMap() const override;
  std::string hash() const override;
  std::string serialise() const override;
  std::string method() const override;
  void setMethod(const std::string &method) override;
  const unsigned char *data(size_t &data_length) const override;
  void setData(const unsigned char *data, size_t data_length) override;
  CacheControl cacheControl() const override;

 private:
  std::string _url;
  std::unordered_map<std::string, std::string> _headers;
  std::string _method;
  unsigned char *_data;
  size_t _data_length;
};

}  // namespace http
}  // namespace nativeformat
