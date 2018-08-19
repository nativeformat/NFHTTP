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

#include <NFHTTP/RequestToken.h>

#include <atomic>

#include "RequestTokenDelegate.h"

namespace nativeformat {
namespace http {

class RequestTokenImplementation : public RequestToken,
                                   public std::enable_shared_from_this<RequestTokenImplementation>,
                                   public RequestTokenDelegate {
 public:
  RequestTokenImplementation(const std::weak_ptr<RequestTokenDelegate> &delegate,
                             const std::string &identifier);
  virtual ~RequestTokenImplementation();

  // RequestToken
  void cancel() override;
  std::string identifier() const override;
  bool cancelled() override;
  std::shared_ptr<RequestToken> createDependentToken() override;
  int dependents() override;

  // RequestTokenDelegate
  void requestTokenDidCancel(const std::shared_ptr<RequestToken> &request_token) override;

 private:
  const std::weak_ptr<RequestTokenDelegate> _delegate;
  const std::string _identifier;

  bool _cancelled;
  std::atomic<int> _dependents;
};

}  // namespace http
}  // namespace nativeformat
