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

#include "CachingDatabase.h"

#include <sqlite3.h>

namespace nativeformat {
namespace http {

class CachingSQLiteDatabase : public CachingDatabase {
public:
  CachingSQLiteDatabase(const std::string &cache_location,
                        const std::weak_ptr<CachingDatabaseDelegate> &delegate);
  virtual ~CachingSQLiteDatabase();

  // CachingDatabase
  std::string cachingType() const override;
  void fetchItemForRequest(
      const std::string &request_identifier,
      std::function<void(ErrorCode, const CacheItem &)> callback) override;
  void storeResponse(
      const std::shared_ptr<Response> &response,
      std::function<void(ErrorCode, const std::shared_ptr<Response> &response)>
          callback) override;
  void prune() override;
  void pinItem(const CacheItem &item,
               const std::string &pin_identifier) override;
  void unpinItem(const CacheItem &item,
                 const std::string &pin_identifier) override;
  void
  removePinnedItemsForIdentifier(const std::string &pin_identifier) override;
  void pinnedItemsForIdentifier(
      const std::string &pin_identifier,
      std::function<void(const std::vector<CacheItem> &)> callback) override;
  void pinningIdentifiers(
      std::function<void(const std::vector<std::string> &)> callback) override;

private:
  static int sqliteSelectHTTPCallback(void *context, int argc, char **argv,
                                      char **column_names);
  static int sqliteReplaceHTTPCallback(void *context, int argc, char **argv,
                                       char **column_names);
  static int sqliteSelectVectorHTTPCallback(void *context, int argc,
                                            char **argv, char **column_names);
  static std::time_t
  timeFromSQLDateTimeString(const std::string &date_time_string);

  sqlite3 *_sqlite_handle;
  const std::weak_ptr<CachingDatabaseDelegate> _delegate;
};

} // namespace http
} // namespace nativeformat
