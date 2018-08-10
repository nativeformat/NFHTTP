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

#include <ctime>
#include <functional>
#include <memory>
#include <string>
#include <vector>

#include "CachingDatabaseDelegate.h"

namespace nativeformat {
namespace http {

typedef struct CacheItem {
  const std::time_t expiry_time;
  const std::time_t last_accessed_time;
  const std::string etag;
  const std::time_t last_modified;
  const std::string response;
  const std::string payload_filename;
  const bool valid;
} CacheItem;

class CachingDatabase {
 public:
  typedef enum : int { ErrorCodeNone } ErrorCode;

  virtual std::string cachingType() const = 0;
  virtual void fetchItemForRequest(const std::string &request_identifier,
                                   std::function<void(ErrorCode, const CacheItem &)> callback) = 0;
  virtual void storeResponse(
      const std::shared_ptr<Response> &response,
      std::function<void(ErrorCode, const std::shared_ptr<Response> &response)> callback) = 0;
  virtual void prune() = 0;
  virtual void pinItem(const CacheItem &item, const std::string &pin_identifier) = 0;
  virtual void unpinItem(const CacheItem &item, const std::string &pin_identifier) = 0;
  virtual void removePinnedItemsForIdentifier(const std::string &pin_identifier) = 0;
  virtual void pinnedItemsForIdentifier(
      const std::string &pin_identifier,
      std::function<void(const std::vector<CacheItem> &)> callback) = 0;
  virtual void pinningIdentifiers(
      std::function<void(const std::vector<std::string> &)> callback) = 0;
};

extern std::shared_ptr<CachingDatabase> createCachingDatabase(
    const std::string &cache_location,
    const std::string &cache_type_hint,
    const std::weak_ptr<CachingDatabaseDelegate> &delegate);

}  // namespace http
}  // namespace nativeformat
