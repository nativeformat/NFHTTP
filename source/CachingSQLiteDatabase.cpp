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
#include "CachingSQLiteDatabase.h"

#include <ctime>
#include <iomanip>
#include <iostream>
#include <locale>
#include <sstream>
#include <string>
#include <vector>

#include <boost/algorithm/string.hpp>

namespace nativeformat {
namespace http {

typedef std::function<void(const std::unordered_map<std::string, std::string> &)> caching_callback;
typedef std::function<void(const std::vector<std::unordered_map<std::string, std::string>> &)>
    caching_vector_callback;

static const std::string http_table_name("http");
static const std::string expiry_column_name("EXPIRY");
static const std::string etag_column_name("ETAG");
static const std::string modified_column_name("MODIFIED");
static const std::string header_hash_column_name("HEADER_HASH");
static const std::string response_serialised_column_name("RESPONSE_SERIALISED");
static const std::string last_accessed_column_name("LAST_ACCESSED");
static const std::string file_size_column_name("FILE_SIZE");
static const std::string current_size_virtual_column_name("CURRENT_SIZE");
static const std::string expires_header_name("Expires");
static const std::string pinned_items_table_name("pinned_items");
static const std::string pin_identifier_column_name("PIN_IDENTIFIER");
static const std::string etag_header_name("ETag");
static const std::string last_modified_header_name("Last-Modified");

static const int maximum_cache_file_size = 524288000;  // 500 MB

CachingSQLiteDatabase::CachingSQLiteDatabase(const std::string &cache_location,
                                             const std::weak_ptr<CachingDatabaseDelegate> &delegate)
    : _delegate(delegate) {
  int sqlite_error = sqlite3_open((cache_location + ".nfhttp").c_str(), &_sqlite_handle);
  if (sqlite_error != SQLITE_OK) {
    printf("SQLite failed to open: %d\n", sqlite_error);
  } else {
    // Create our tables
    std::string create_tables_query =
        "CREATE TABLE IF NOT EXISTS " + http_table_name + "(" + header_hash_column_name +
        " STRING PRIMARY KEY NOT NULL, " + expiry_column_name + " DATETIME NOT NULL, " +
        etag_column_name + " STRING, " + modified_column_name + " DATETIME NOT NULL, " +
        response_serialised_column_name + " STRING NOT NULL, " + last_accessed_column_name +
        " DATETIME NOT NULL, " + file_size_column_name + " INT NOT NULL);";
    create_tables_query += "CREATE TABLE IF NOT EXISTS " + pinned_items_table_name + " (" +
                           header_hash_column_name + " STRING NOT NULL, " +
                           pin_identifier_column_name + " STRING NOT NULL, UNIQUE(" +
                           header_hash_column_name + ", " + pin_identifier_column_name +
                           "), FOREIGN KEY(" + header_hash_column_name + ") REFERENCES " +
                           http_table_name + "(" + header_hash_column_name + "));";
    char *error_message = nullptr;
    sqlite_error =
        sqlite3_exec(_sqlite_handle, create_tables_query.c_str(), nullptr, this, &error_message);
    if (sqlite_error != SQLITE_OK) {
      printf("Failed to create the tables: %d %s\n", sqlite_error, error_message);
    }
  }
}

CachingSQLiteDatabase::~CachingSQLiteDatabase() {
  if (_sqlite_handle != nullptr) {
    sqlite3_close(_sqlite_handle);
  }
}

std::string CachingSQLiteDatabase::cachingType() const {
  return "sqlite";
}

void CachingSQLiteDatabase::fetchItemForRequest(
    const std::string &request_identifier,
    std::function<void(ErrorCode, const CacheItem &)> callback) {
  bool executed = false;
  caching_callback cache_function = [callback, this, &executed](
                                        const std::unordered_map<std::string, std::string> &map) {
    std::string header_hash = map.at(header_hash_column_name);
    char *error_message = nullptr;
    sqlite3_exec(_sqlite_handle,
                 ("UPDATE " + http_table_name + " SET " + last_accessed_column_name +
                  " = date('now') WHERE " + header_hash_column_name + " = '" + header_hash + "'")
                     .c_str(),
                 nullptr,
                 nullptr,
                 &error_message);

    CacheItem item = {timeFromSQLDateTimeString(map.at(expiry_column_name)),
                      timeFromSQLDateTimeString(map.at(modified_column_name)),
                      map.at(etag_column_name),
                      timeFromSQLDateTimeString(map.at(last_accessed_column_name)),
                      map.at(response_serialised_column_name),
                      map.at(header_hash_column_name),
                      true};
    callback(ErrorCodeNone, item);
    executed = true;
  };

  char *error_message = nullptr;
  int error = sqlite3_exec(
      _sqlite_handle,
      ("SELECT " + header_hash_column_name + ", " + expiry_column_name + ", " + etag_column_name +
       ", " + modified_column_name + ", " + response_serialised_column_name + ", " +
       last_accessed_column_name + " FROM " + http_table_name + " WHERE " +
       header_hash_column_name + " = '" + request_identifier + "'")
          .c_str(),
      &sqliteSelectHTTPCallback,
      &cache_function,
      &error_message);
  if (error != SQLITE_OK || !executed) {
    const CacheItem cache_item = {0, 0, "", 0, "", "", false};
    callback((ErrorCode)error, cache_item);
  }
}

void CachingSQLiteDatabase::storeResponse(
    const std::shared_ptr<Response> &response,
    std::function<void(ErrorCode, const std::shared_ptr<Response> &response)> callback) {
  bool executed = false;
  caching_callback cache_function =
      [callback, response, &executed](const std::unordered_map<std::string, std::string> &map) {
        callback(ErrorCodeNone, response);
        executed = true;
      };

  // Determine expiry time
  const auto &header_map = response->headerMap();
  Response::CacheControl cache_control = response->cacheControl();
  std::string expiry_value =
      "date('now', '+" + std::to_string(cache_control.max_age) + " seconds')";
  if (cache_control.max_age == 0) {
    // Perhaps we have an expires header
    if (header_map.find(expires_header_name) != header_map.end()) {
      expiry_value = "date('" + header_map.at(expires_header_name) + "')";
    }
  }

  // Store response
  size_t data_length = 0;
  response->data(data_length);
  char *error_message = nullptr;
  std::string etag = "";
  if (header_map.find(etag_header_name) != header_map.end()) {
    etag = header_map.at(etag_header_name);
  }
  std::string last_modified = "";
  if (header_map.find(last_modified_header_name) != header_map.end()) {
    last_modified = header_map.at(last_modified_header_name);
  }
  int error =
      sqlite3_exec(_sqlite_handle,
                   ("REPLACE INTO " + http_table_name + " (" + header_hash_column_name + ", " +
                    expiry_column_name + ", " + etag_column_name + ", " + modified_column_name +
                    ", " + response_serialised_column_name + ", " + last_accessed_column_name +
                    ", " + file_size_column_name + ") VALUES ('" + response->request()->hash() +
                    "', " + expiry_value + ", '" + etag + "', '" + last_modified + "', '" +
                    response->serialise() + "', date('now'), " + std::to_string(data_length) + ");")
                       .c_str(),
                   &sqliteReplaceHTTPCallback,
                   &cache_function,
                   &error_message);
  if (error != SQLITE_OK || !executed) {
    callback((ErrorCode)error, response);
  }
}

void CachingSQLiteDatabase::prune() {
  caching_callback cache_function = [this](
                                        const std::unordered_map<std::string, std::string> &map) {
    int current_size = std::stoi(map.at(current_size_virtual_column_name));
    if (current_size <= maximum_cache_file_size) {
      return;
    }

    caching_vector_callback cache_function =
        [this,
         current_size](const std::vector<std::unordered_map<std::string, std::string>> &results) {
          int local_current_size = current_size;
          for (const auto &result_map : results) {
            std::string header_hash = result_map.at(header_hash_column_name);
            char *error_message = nullptr;
            int error_code = sqlite3_exec(_sqlite_handle,
                                          ("DELETE FROM " + http_table_name + " WHERE " +
                                           header_hash_column_name + " = '" + header_hash + "'")
                                              .c_str(),
                                          nullptr,
                                          nullptr,
                                          &error_message);
            if (error_code == SQLITE_OK) {
              if (auto delegate = _delegate.lock()) {
                delegate->deleteDatabaseFile(header_hash);
              }
            }
            local_current_size -= std::stoi(result_map.at(file_size_column_name));
            if (local_current_size <= maximum_cache_file_size) {
              break;
            }
          }

          if (local_current_size <= maximum_cache_file_size) {
            return;
          }

          // Perform an LRU prune
          caching_vector_callback *cache_function = new caching_vector_callback(
              [local_current_size,
               this](const std::vector<std::unordered_map<std::string, std::string>> &results) {
                size_t lru_current_size = local_current_size;
                for (const auto &result_map : results) {
                  std::string header_hash = result_map.at(header_hash_column_name);
                  char *error_message = nullptr;
                  int error_code =
                      sqlite3_exec(_sqlite_handle,
                                   ("DELETE FROM " + http_table_name + " WHERE " +
                                    header_hash_column_name + " = '" + header_hash + "'")
                                       .c_str(),
                                   nullptr,
                                   nullptr,
                                   &error_message);
                  if (error_code == SQLITE_OK) {
                    if (auto delegate = _delegate.lock()) {
                      delegate->deleteDatabaseFile(header_hash);
                    }
                  }
                  lru_current_size -= std::stoi(result_map.at(file_size_column_name));
                  if (lru_current_size <= maximum_cache_file_size) {
                    break;
                  }
                }
              });
          char *error_message = nullptr;
          sqlite3_exec(_sqlite_handle,
                       ("SELECT " + header_hash_column_name + ", " + file_size_column_name +
                        " FROM " + http_table_name + " ORDER BY " + last_accessed_column_name)
                           .c_str(),
                       &sqliteSelectVectorHTTPCallback,
                       &cache_function,
                       &error_message);
        };

    // Find the old expired content
    char *error_message = nullptr;
    sqlite3_exec(_sqlite_handle,
                 ("SELECT " + header_hash_column_name + ", " + file_size_column_name + " FROM " +
                  http_table_name + " ORDER BY " + expiry_column_name + " ASC")
                     .c_str(),
                 &sqliteSelectVectorHTTPCallback,
                 &cache_function,
                 &error_message);
  };

  char *error_message = nullptr;
  sqlite3_exec(_sqlite_handle,
               ("SELECT SUM(" + file_size_column_name + ") AS " + current_size_virtual_column_name +
                " FROM " + http_table_name)
                   .c_str(),
               &sqliteSelectHTTPCallback,
               &cache_function,
               &error_message);
}

void CachingSQLiteDatabase::pinItem(const CacheItem &item, const std::string &pin_identifier) {
  char *error_message = nullptr;
  sqlite3_exec(_sqlite_handle,
               ("REPLACE INTO " + pinned_items_table_name + " (" + header_hash_column_name + ", " +
                pin_identifier_column_name + ") VALUES ('" + item.payload_filename + "', '" +
                pin_identifier + "')")
                   .c_str(),
               nullptr,
               nullptr,
               &error_message);
}

void CachingSQLiteDatabase::unpinItem(const CacheItem &item, const std::string &pin_identifier) {
  char *error_message = nullptr;
  sqlite3_exec(_sqlite_handle,
               ("DELETE FROM " + pinned_items_table_name + " WHERE " + header_hash_column_name +
                " = '" + item.payload_filename + "' AND " + pin_identifier_column_name + " = '" +
                pin_identifier + "'")
                   .c_str(),
               nullptr,
               nullptr,
               &error_message);
}

void CachingSQLiteDatabase::removePinnedItemsForIdentifier(const std::string &pin_identifier) {
  char *error_message = nullptr;
  sqlite3_exec(_sqlite_handle,
               ("DELETE FROM " + pinned_items_table_name + " WHERE " + pin_identifier_column_name +
                " = '" + pin_identifier + "'")
                   .c_str(),
               nullptr,
               nullptr,
               &error_message);
}

void CachingSQLiteDatabase::pinnedItemsForIdentifier(
    const std::string &pin_identifier,
    std::function<void(const std::vector<CacheItem> &)> callback) {
  caching_vector_callback sqlite_callback =
      [callback](const std::vector<std::unordered_map<std::string, std::string>> &results) {
        std::vector<CacheItem> items;
        for (const auto &result : results) {
          items.push_back({timeFromSQLDateTimeString(result.at(expiry_column_name)),
                           timeFromSQLDateTimeString(result.at(modified_column_name)),
                           result.at(etag_column_name),
                           timeFromSQLDateTimeString(result.at(last_accessed_column_name)),
                           result.at(response_serialised_column_name),
                           result.at(header_hash_column_name),
                           true});
        }
        callback(items);
      };

  char *error_message = nullptr;
  sqlite3_exec(
      _sqlite_handle,
      ("SELECT " + http_table_name + "." + expiry_column_name + " AS " + expiry_column_name + ", " +
       http_table_name + "." + etag_column_name + " AS " + etag_column_name + ", " +
       http_table_name + "." + modified_column_name + " AS " + modified_column_name + ", " +
       http_table_name + "." + header_hash_column_name + " AS " + header_hash_column_name + ", " +
       http_table_name + "." + response_serialised_column_name + " AS " +
       response_serialised_column_name + ", " + http_table_name + "." + last_accessed_column_name +
       " AS " + last_accessed_column_name + " FROM " + http_table_name + ", " +
       pinned_items_table_name + " WHERE " + http_table_name + "." + header_hash_column_name +
       " = " + pinned_items_table_name + "." + header_hash_column_name + " AND " +
       pinned_items_table_name + "." + pin_identifier_column_name + " = '" + pin_identifier + "'")
          .c_str(),
      &sqliteSelectVectorHTTPCallback,
      &sqlite_callback,
      &error_message);
}

void CachingSQLiteDatabase::pinningIdentifiers(
    std::function<void(const std::vector<std::string> &)> callback) {
  caching_vector_callback sqlite_callback =
      [callback](const std::vector<std::unordered_map<std::string, std::string>> &results) {
        std::vector<std::string> pinned_identifiers;
        for (const auto &result : results) {
          pinned_identifiers.push_back(result.at(pin_identifier_column_name));
        }
        callback(pinned_identifiers);
      };

  char *error_message = nullptr;
  sqlite3_exec(
      _sqlite_handle,
      ("SELECT UNIQUE(" + pin_identifier_column_name + ") FROM " + pinned_items_table_name).c_str(),
      &sqliteSelectVectorHTTPCallback,
      &sqlite_callback,
      &error_message);
}

int CachingSQLiteDatabase::sqliteSelectHTTPCallback(void *context,
                                                    int argc,
                                                    char **argv,
                                                    char **column_names) {
  caching_callback *cache_function = (caching_callback *)context;
  std::unordered_map<std::string, std::string> map;
  for (int i = 0; i < argc; ++i) {
    if (argv[i] == nullptr) {
      continue;
    }
    map[column_names[i]] = argv[i];
  }
  (*cache_function)(map);
  return SQLITE_OK;
}

int CachingSQLiteDatabase::sqliteReplaceHTTPCallback(void *context,
                                                     int argc,
                                                     char **argv,
                                                     char **column_names) {
  caching_callback *cache_function = (caching_callback *)context;
  (*cache_function)({});
  return SQLITE_OK;
}

int CachingSQLiteDatabase::sqliteSelectVectorHTTPCallback(void *context,
                                                          int argc,
                                                          char **argv,
                                                          char **column_names) {
  caching_vector_callback *cache_function = (caching_vector_callback *)context;
  std::vector<std::unordered_map<std::string, std::string>> result_vector;
  std::unordered_map<std::string, std::string> result;
  for (int i = 0; i < argc; ++i) {
    if (result.find(column_names[i]) != result.end()) {
      result_vector.push_back(result);
      result.clear();
    }
    result[column_names[i]] = argv[i];
  }
  result_vector.push_back(result);
  (*cache_function)(result_vector);
  return SQLITE_OK;
}

std::time_t CachingSQLiteDatabase::timeFromSQLDateTimeString(const std::string &date_time_string) {
  std::vector<std::string> space_separated_strings;
  boost::split(date_time_string, space_separated_strings, boost::is_any_of(" "));
  if (space_separated_strings.size() != 2) {
    return std::time(0);
  }
  std::vector<std::string> date_separated_strings;
  boost::split(space_separated_strings[0], date_separated_strings, boost::is_any_of("-"));
  if (date_separated_strings.size() != 3) {
    return std::time(0);
  }
  std::vector<std::string> time_separated_strings;
  boost::split(space_separated_strings[1], time_separated_strings, boost::is_any_of(":"));
  if (time_separated_strings.size() != 3) {
    return std::time(0);
  }
  struct std::tm *timeinfo;
  std::time_t rawtime;
  std::time(&rawtime);
  timeinfo = std::gmtime(&rawtime);
  timeinfo->tm_year = std::stoi(date_separated_strings[0]) - 1900;
  timeinfo->tm_mon = std::stoi(date_separated_strings[1]) - 1;
  timeinfo->tm_mday = std::stoi(date_separated_strings[2]);
  timeinfo->tm_hour = std::stoi(time_separated_strings[0]);
  timeinfo->tm_min = std::stoi(time_separated_strings[1]);
  timeinfo->tm_sec = std::stoi(time_separated_strings[2]);
  return std::mktime(timeinfo);
}

}  // namespace http
}  // namespace nativeformat
