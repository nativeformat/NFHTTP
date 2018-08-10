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

#include <NFHTTP/Response.h>

#include <memory>
#include <string>
#include <unordered_map>

namespace nativeformat {
namespace http {

class ResponseImplementation : public Response {
 public:
  ResponseImplementation(const std::shared_ptr<Request> &request,
                         const unsigned char *data,
                         size_t data_length,
                         StatusCode status_code,
                         bool cancelled);
  ResponseImplementation(const std::string &serialised,
                         const unsigned char *data,
                         size_t data_length,
                         const std::shared_ptr<Response> &response = nullptr);
  virtual ~ResponseImplementation();

  // Response
  const std::shared_ptr<Request> request() const override;
  const unsigned char *data(size_t &data_length) const override;
  StatusCode statusCode() const override;
  bool cancelled() const override;
  std::string serialise() const override;
  std::string operator[](const std::string &header_name) const override;
  std::string &operator[](const std::string &header_name) override;
  std::unordered_map<std::string, std::string> &headerMap() override;
  std::unordered_map<std::string, std::string> headerMap() const override;
  CacheControl cacheControl() const override;
  std::unordered_map<std::string, std::string> metadata() const override;
  void setMetadata(const std::string &key, const std::string &value) override;

 private:
  std::shared_ptr<Request> _request;
  unsigned char *_data;
  const size_t _data_length;
  StatusCode _status_code;
  const bool _cancelled;
  std::unordered_map<std::string, std::string> _headers;
  std::unordered_map<std::string, std::string> _metadata;
};

}  // namespace http
}  // namespace nativeformat
