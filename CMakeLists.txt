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
cmake_minimum_required(VERSION 3.6)

project(NFHTTP)

set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

if(NOT WIN32)
  set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wno-deprecated-declarations")
endif()

if(LLVM_STDLIB)
  set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -stdlib=libc++ \
    -Wno-tautological-undefined-compare")
endif()

set(NFHTTP_INCLUDE_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/include")
set(NFHTTP_LIBRARIES_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/libraries")

if(USE_ADDRESS_SANITIZER)
  message("Using Address & Leak Sanitizer")
  set(
    CMAKE_CXX_FLAGS
    "${CMAKE_CXX_FLAGS} -fsanitize=address -g -fno-omit-frame-pointer")
  set(
    CMAKE_EXE_LINKER_FLAGS
    "${CMAKE_EXE_LINKER_FLAGS} -fsanitize=address -g -fno-omit-frame-pointer")
endif()

if(CODE_COVERAGE)
  message("Using Code Coverage")
  set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fprofile-arcs -ftest-coverage")
  set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} --coverage")
endif()

if(NOT DEFINED USE_CURL)
  if(CMAKE_SYSTEM_NAME MATCHES "Linux" OR ANDROID)
    set(USE_CURL TRUE CACHE BOOL "Build with curl")
  else()
    set(USE_CURL FALSE CACHE BOOL "Build with curl")
  endif()
endif()

if(USE_CURL)
  add_definitions(-DUSE_CURL=1)
endif()

if(NOT DEFINED USE_CPPRESTSDK)
  if(WIN32)
    set(USE_CPPRESTSDK TRUE CACHE BOOL "Build with Microsoft's C++ Rest SDK")
  else()
    set(USE_CPPRESTSDK FALSE CACHE BOOL "Build with Microsoft's C++ Rest SDK")
  endif()
endif()

if(USE_CPPRESTSDK)
  add_definitions(-DUSE_CPPRESTSDK=1)
endif()

if(WIN32)
  set(WINDOWS_FLAGS "/W3")
  set(WINDOWS_FLAGS "${WINDOWS_FLAGS} /WX")
  set(WINDOWS_FLAGS "${WINDOWS_FLAGS} /bigobj")
  set(WINDOWS_FLAGS "${WINDOWS_FLAGS} /D_CRT_SECURE_NO_WARNINGS=1")
  set(WINDOWS_FLAGS "${WINDOWS_FLAGS} /wd4003")
  set(WINDOWS_FLAGS "${WINDOWS_FLAGS} /wd4018")
  set(WINDOWS_FLAGS "${WINDOWS_FLAGS} /wd4091")
  set(WINDOWS_FLAGS "${WINDOWS_FLAGS} /wd4200")
  set(WINDOWS_FLAGS "${WINDOWS_FLAGS} /wd4250")
  set(WINDOWS_FLAGS "${WINDOWS_FLAGS} /wd4275")
  set(WINDOWS_FLAGS "${WINDOWS_FLAGS} /wd4355")
  set(WINDOWS_FLAGS "${WINDOWS_FLAGS} /wd4520")
  set(WINDOWS_FLAGS "${WINDOWS_FLAGS} /wd4530")
  set(WINDOWS_FLAGS "${WINDOWS_FLAGS} /wd4146")
  set(WINDOWS_FLAGS "${WINDOWS_FLAGS} /we4053")
  set(WINDOWS_FLAGS "${WINDOWS_FLAGS} /we4063")
  set(WINDOWS_FLAGS "${WINDOWS_FLAGS} /we4064")
  set(WINDOWS_FLAGS "${WINDOWS_FLAGS} /wd4503")
  set(WINDOWS_FLAGS "${WINDOWS_FLAGS} /DWIN32")
  set(WINDOWS_FLAGS "${WINDOWS_FLAGS} /DUNICODE")
  set(WINDOWS_FLAGS "${WINDOWS_FLAGS} /D_UNICODE")
  set(WINDOWS_FLAGS "${WINDOWS_FLAGS} /D_WINDOWS")
  set(WINDOWS_FLAGS "${WINDOWS_FLAGS} /DNOMINMAX")
  set(WINDOWS_FLAGS "${WINDOWS_FLAGS} /D_WIN32_IE=0x0700")
  set(WINDOWS_FLAGS "${WINDOWS_FLAGS} /D_WIN32_WINNT=0x0601")
  set(WINDOWS_FLAGS "${WINDOWS_FLAGS} /wd4447")
  set(WINDOWS_LINKER_FLAGS "/DYNAMICBASE:NO")
  set(WINDOWS_LINKER_FLAGS "${WINDOWS_LINKER_FLAGS} /INCREMENTAL:NO")
  set(WINDOWS_LINKER_FLAGS "${WINDOWS_LINKER_FLAGS} /OPT:ICF")
  set(WINDOWS_LINKER_FLAGS "${WINDOWS_LINKER_FLAGS} /OPT:REF")
  set(WINDOWS_LINKER_FLAGS "${WINDOWS_LINKER_FLAGS} /NXCOMPAT:NO")

  # TODO fix and use windows flags
  set(CMAKE_EXE_LINKER_FLAGS
    "${CMAKE_EXE_LINKER_FLAGS} ${WINDOWS_LINKER_FLAGS}")
endif()

set(OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/output")
message("OUTPUT_DIRECTORY: ${OUTPUT_DIRECTORY}")
execute_process(COMMAND python
  "${CMAKE_CURRENT_SOURCE_DIR}/tools/generate-version.py"
  "${OUTPUT_DIRECTORY}"
  WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR})

add_subdirectory(libraries)
add_subdirectory(source)

message(STATUS "********** Build configuration ************")
message(STATUS "Compiling for ${CMAKE_SYSTEM_NAME}")
message(STATUS "Configuration: ${CMAKE_BUILD_TYPE}")
message(STATUS "C Compiler: ${CMAKE_C_COMPILER}")
message(STATUS "C++ Compiler: ${CMAKE_CXX_COMPILER}")
