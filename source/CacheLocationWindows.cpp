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

#ifdef _WIN32

#include <shlobj.h>
#include <sstream>
#include <string>
#include <wchar.h>

namespace nativeformat {
namespace http {

std::string standardCacheLocation() {
  wchar_t *localAppData = NULL;
  SHGetKnownFolderPath(FOLDERID_LocalAppData, 0, NULL, &localAppData);
  std::stringstream ss;
  ss << localAppData << "/NativeFormat/";
  CreateDirectory(ss.str().c_str(), NULL);
  CoTaskMemFree(static_cast<void *>(localAppData));
  return ss.str();
}

} // namespace http
} // namespace nativeformat

#endif
