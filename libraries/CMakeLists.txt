# Copyright (c) 2018 Spotify AB.
#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
add_library(sqlite "${CMAKE_CURRENT_SOURCE_DIR}/sqlite/sqlite3.c")
target_compile_definitions(sqlite PUBLIC -DSQLITE_THREADSAFE=2)

find_package(OpenSSL 1.0.0 REQUIRED)
find_package(Boost 1.54.0 REQUIRED)
find_package(CURL REQUIRED)

# Add json
set(JSON_BuildTests OFF CACHE BOOL "Don't build JSON tests" FORCE)
add_subdirectory(json)

# Conditionally add Microsoft's C++ Rest SDK
if(USE_CPPRESTSDK)
  set(CPPREST_INCLUDE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/cpprestsdk/Release/include" CACHE STRING "C++ REST SDK Includes" FORCE)
  set(BOOST_LIBRARYDIR ${BOOST_LIB_DIR})
  set(CPPREST_INSTALL OFF CACHE BOOL "Don't install" FORCE)
  set(CPPREST_INSTALL_HEADERS OFF CACHE BOOL "Don't install headers" FORCE)
  set(BUILD_SHARED_LIBS OFF CACHE BOOL "Build cpprest as a static lib" FORCE)
  set(CPPREST_EXCLUDE_COMPRESSION ON CACHE BOOL "Exclude compression functionality." FORCE)
  add_definitions(-DSSL_R_SHORT_READ)
  add_subdirectory(cpprestsdk/Release)
endif()
