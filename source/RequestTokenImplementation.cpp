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
#include "RequestTokenImplementation.h"

namespace nativeformat {
namespace http {

RequestTokenImplementation::RequestTokenImplementation(
    const std::weak_ptr<RequestTokenDelegate> &delegate, const std::string &identifier)
    : _delegate(delegate), _identifier(identifier), _cancelled(false), _dependents(0) {}

RequestTokenImplementation::~RequestTokenImplementation() {}

void RequestTokenImplementation::cancel() {
  _cancelled = true;
  if (auto delegate = _delegate.lock()) {
    delegate->requestTokenDidCancel(shared_from_this());
  }
}

std::string RequestTokenImplementation::identifier() const {
  return _identifier;
}

bool RequestTokenImplementation::cancelled() {
  return _cancelled && dependents() == 0;
}

std::shared_ptr<RequestToken> RequestTokenImplementation::createDependentToken() {
  _dependents++;
  return std::make_shared<RequestTokenImplementation>(shared_from_this(), _identifier);
}

int RequestTokenImplementation::dependents() {
  return _dependents;
}

void RequestTokenImplementation::requestTokenDidCancel(
    const std::shared_ptr<RequestToken> &request_token) {
  _dependents--;
}

}  // namespace http
}  // namespace nativeformat
