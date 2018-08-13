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
set(SOURCE_FILES
  Client.cpp
  CachingClient.h
  CachingClient.cpp
  Request.cpp
  RequestImplementation.cpp
  RequestTokenImplementation.h
  RequestTokenImplementation.cpp
  RequestTokenDelegate.h
  ResponseImplementation.cpp
  sha256.h
  sha256.cpp
  CachingDatabase.h
  CachingDatabase.cpp
  CachingSQLiteDatabase.h
  CachingSQLiteDatabase.cpp
  CachingDatabaseDelegate.h
  CacheLocationLinux.cpp
  CacheLocationWindows.cpp
  ClientModifierImplementation.h
  ClientModifierImplementation.cpp
  RequestImplementation.h
  ClientMultiRequestImplementation.h
  ClientMultiRequestImplementation.cpp
  NFHTTP.cpp)

if(${CMAKE_SYSTEM_NAME} MATCHES "Darwin" AND NOT ANDROID)
  list(APPEND
    SOURCE_FILES
    CacheLocationApple.mm
    ClientNSURLSession.h
    ClientNSURLSession.mm)
endif()

if(USE_CURL)
  list(APPEND
    SOURCE_FILES
    ClientCurl.h
    ClientCurl.cpp)

  find_path(CURL_INCLUDE_DIR NAMES curl/curl.h)
  mark_as_advanced(CURL_INCLUDE_DIR)
endif()

if(USE_CPPRESTSDK)
  list(APPEND
    SOURCE_FILES
    ClientCpprestsdk.h
    ClientCpprestsdk.cpp)
endif()

add_library(NFHTTP "${NFHTTP_INCLUDE_DIRECTORY}/NFHTTP/Client.h"
  "${NFHTTP_INCLUDE_DIRECTORY}/NFHTTP/Request.h"
  "${NFHTTP_INCLUDE_DIRECTORY}/NFHTTP/RequestToken.h"
  "${NFHTTP_INCLUDE_DIRECTORY}/NFHTTP/Response.h"
  "${NFHTTP_INCLUDE_DIRECTORY}/NFHTTP/ResponseImplementation.h"
  "${NFHTTP_INCLUDE_DIRECTORY}/NFHTTP/NFHTTP.h"
  ${SOURCE_FILES})


target_include_directories(NFHTTP PUBLIC "${NFHTTP_INCLUDE_DIRECTORY}"
  "${NFHTTP_LIBRARIES_DIRECTORY}/sqlite"
  "${NFHTTP_LIBRARIES_DIRECTORY}/curl/include"
  ${CPPREST_INCLUDE_DIR}
  "${CMAKE_BINARY_DIR}/output")

if(WIN32)
  set(LINK_LIBRARIES sqlite)
else()
  set(LINK_LIBRARIES sqlite pthread)
endif()

add_executable(NFHTTPCLI NFHTTPCLI.cpp)
target_include_directories(NFHTTPCLI PUBLIC "${NFHTTP_INCLUDE_DIRECTORY}"
  "${NFHTTP_LIBRARIES_DIRECTORY}/sqlite"
  "${NFHTTP_LIBRARIES_DIRECTORY}/curl/include"
  ${CPPREST_INCLUDE_DIR})

if(USE_CURL)
  find_package(CURL REQUIRED)
  list(APPEND LINK_LIBRARIES ${CURL_LIBRARIES})
endif()

if(USE_CPPRESTSDK)
  list(APPEND LINK_LIBRARIES cpprest)
endif()

if(${CMAKE_SYSTEM_NAME} MATCHES "Darwin")
  find_library(FOUNDATION Foundation)
  list(APPEND LINK_LIBRARIES ${FOUNDATION})
  set_source_files_properties(ClientNSURLSession.mm
    PROPERTIES COMPILE_FLAGS "-fobjc-arc")
  set_source_files_properties(CacheLocationApple.mm
    PROPERTIES COMPILE_FLAGS "-fobjc-arc")
endif()

target_link_libraries(NFHTTP PUBLIC ${LINK_LIBRARIES} nlohmann_json)
target_link_libraries(NFHTTPCLI NFHTTP nlohmann_json)

if(USE_CURL)
  target_compile_definitions(NFHTTP PRIVATE USE_CURL=1)
endif()
