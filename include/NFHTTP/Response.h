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

#include <memory>

namespace nativeformat {
namespace http {

typedef enum : int {
  StatusCodeInvalid = 0,
  // Informational
  StatusCodeContinue = 100,
  StatusCodeSwitchProtocols = 101,
  // Successful
  StatusCodeOK = 200,
  StatusCodeCreated = 201,
  StatusCodeAccepted = 202,
  StatusCodeNonAuthoritiveInformation = 203,
  StatusCodeNoContent = 204,
  StatusCodeResetContent = 205,
  StatusCodePartialContent = 206,
  // Redirection
  StatusCodeMovedMultipleChoices = 300,
  StatusCodeMovedPermanently = 301,
  StatusCodeFound = 302,
  StatusCodeSeeOther = 303,
  StatusCodeNotModified = 304,
  StatusCodeUseProxy = 305,
  StatusCodeUnused = 306,
  StatusCodeTemporaryRedirect = 307,
  // Client Error
  StatusCodeBadRequest = 400,
  StatusCodeUnauthorised = 401,
  StatusCodePaymentRequired = 402,
  StatusCodeForbidden = 403,
  StatusCodeNotFound = 404,
  StatusCodeMethodNotAllowed = 405,
  StatusCodeNotAcceptable = 406,
  StatusCodeProxyAuthenticationRequired = 407,
  StatusCodeRequestTimeout = 408,
  StatusCodeConflict = 409,
  StatusCodeGone = 410,
  StatusCodeLengthRequired = 411,
  StatusCodePreconditionFailed = 412,
  StatusCodeRequestEntityTooLarge = 413,
  StatusCodeRequestURITooLong = 414,
  StatusCodeUnsupportedMediaTypes = 415,
  StatusCodeRequestRangeUnsatisfied = 416,
  StatusCodeExpectationFail = 417,
  // Server Error
  StatusCodeInternalServerError = 500,
  StatusCodeNotImplemented = 501,
  StatusCodeBadGateway = 502,
  StatusCodeServiceUnavailable = 503,
  StatusCodeGatewayTimeout = 504,
  StatusCodeHTTPVersionNotSupported = 505
} StatusCode;

class Response {
 public:
  typedef struct CacheControl {
    const bool must_revalidate;
    const bool no_cache;
    const bool no_store;
    const bool no_transform;
    const bool access_control_public;
    const bool access_control_private;
    const bool proxy_revalidate;
    const int max_age;
    const int shared_max_age;
  } CacheControl;

  virtual const std::shared_ptr<Request> request() const = 0;
  virtual const unsigned char *data(size_t &data_length) const = 0;
  virtual StatusCode statusCode() const = 0;
  virtual bool cancelled() const = 0;
  virtual std::string serialise() const = 0;
  virtual std::string operator[](const std::string &header_name) const = 0;
  virtual std::string &operator[](const std::string &header_name) = 0;
  virtual std::unordered_map<std::string, std::string> &headerMap() = 0;
  virtual std::unordered_map<std::string, std::string> headerMap() const = 0;
  virtual CacheControl cacheControl() const = 0;
  virtual std::unordered_map<std::string, std::string> metadata() const = 0;
  virtual void setMetadata(const std::string &key, const std::string &value) = 0;
};

}  // namespace http
}  // namespace nativeformat
