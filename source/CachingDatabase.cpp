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
#include "CachingDatabase.h"

#include "CachingSQLiteDatabase.h"

namespace nativeformat {
namespace http {

std::shared_ptr<CachingDatabase> createCachingDatabase(
    const std::string &cache_location,
    const std::string &cache_type_hint,
    const std::weak_ptr<CachingDatabaseDelegate> &delegate) {
  return std::make_shared<CachingSQLiteDatabase>(cache_location, delegate);
}

}  // namespace http
}  // namespace nativeformat
