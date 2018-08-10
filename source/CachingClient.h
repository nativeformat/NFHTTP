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

#include <NFHTTP/Client.h>

#include <atomic>
#include <memory>
#include <thread>
#include <unordered_map>

#include "CachingDatabase.h"
#include "RequestTokenDelegate.h"

namespace nativeformat {
namespace http {

class CachingClient : public Client,
                      public RequestTokenDelegate,
                      public std::enable_shared_from_this<CachingClient>,
                      public CachingDatabaseDelegate {
 public:
  CachingClient(const std::shared_ptr<Client> &client, const std::string &cache_location);
  virtual ~CachingClient();

  // RequestTokenDelegate
  void requestTokenDidCancel(const std::shared_ptr<RequestToken> &request_token) override;

  // CachingDatabaseDelegate
  void deleteDatabaseFile(const std::string &header_hash) override;

  // Client
  std::shared_ptr<RequestToken> performRequest(
      const std::shared_ptr<Request> &request,
      std::function<void(const std::shared_ptr<Response> &)> callback) override;
  void pinResponse(const std::shared_ptr<Response> &response,
                   const std::string &pin_identifier) override;
  void unpinResponse(const std::shared_ptr<Response> &response,
                     const std::string &pin_identifier) override;
  void removePinnedResponseForIdentifier(const std::string &pin_identifier) override;
  void pinnedResponsesForIdentifier(
      const std::string &pin_identifier,
      std::function<void(const std::vector<std::shared_ptr<Response>> &)> callback) override;
  void pinningIdentifiers(
      std::function<void(const std::vector<std::string> &identifiers)> callback) override;

  void initialise();

 private:
  static void pruneThread(CachingClient *client);

  const std::shared_ptr<Response> responseFromCacheItem(
      const CacheItem &item, const std::shared_ptr<Response> &response = nullptr) const;
  bool shouldCacheRequest(const std::shared_ptr<Request> &request);

  const std::shared_ptr<Client> _client;
  const std::string _cache_location;
  std::thread _prune_thread;
  std::shared_ptr<CachingDatabase> _database;

  std::unordered_map<std::shared_ptr<RequestToken>, std::weak_ptr<RequestToken>> _tokens;
  std::atomic<bool> _shutdown_prune_thread;
};

}  // namespace http
}  // namespace nativeformat
