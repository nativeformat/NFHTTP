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

#ifdef __linux__
#include <pwd.h>
#include <sstream>
#include <string>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

namespace nativeformat {
namespace http {

std::string standardCacheLocation() {
  struct passwd *pw = getpwuid(getuid());
  const char *homedir = pw->pw_dir;
  std::stringstream ss;
  ss << homedir << "/.cache";
  std::string cachedir = ss.str();
  struct stat st = {0};
  if (stat(cachedir.c_str(), &st) == -1) {
    mkdir(cachedir.c_str(), 0700);
  }
  return cachedir;
}

} // namespace http
} // namespace nativeformat
#endif
