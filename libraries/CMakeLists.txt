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

# Add Boost
set(BOOST_ROOT "$ENV{BOOST_ROOT}" CACHE INTERNAL "Boost Root Directory")
set(BOOST_DIR "${BOOST_ROOT}" CACHE INTERNAL "Boost Directory")
set(Boost_INCLUDE_DIR "${BOOST_ROOT}" CACHE INTERNAL "Boost Include Directory")
set(BOOST_LIB_DIR "${BOOST_ROOT}/libs" CACHE INTERNAL "Boost Library Directory")
set(BOOST_GRAPH_SRC_DIR "${BOOST_LIB_DIR}/graph/src")
set(BOOST_PROGRAM_OPTIONS_SRC_DIR "${BOOST_LIB_DIR}/program_options/src")
set(BOOST_THREAD_SRC_DIR "${BOOST_LIB_DIR}/thread/src")
set(BOOST_CHRONO_SRC_DIR "${BOOST_LIB_DIR}/chrono/src")
set(BOOST_SYSTEM_SRC_DIR "${BOOST_LIB_DIR}/system/src")
set(BOOST_TEST_SRC_DIR "${BOOST_LIB_DIR}/test/src")
set(BOOST_RANDOM_SRC_DIR "${BOOST_LIB_DIR}/random/src")
set(BOOST_FILESYSTEM_SRC_DIR "${BOOST_LIB_DIR}/filesystem/src")
set(BOOST_ATOMIC_SRC_DIR "${BOOST_LIB_DIR}/atomic/src")
set(BOOST_DATE_TIME_SRC_DIR "${BOOST_LIB_DIR}/date_time/src")
set(BOOST_REGEX_SRC_DIR "${BOOST_LIB_DIR}/regex/src")
add_library(boost_graph STATIC
  ${BOOST_GRAPH_SRC_DIR}/graphml.cpp
  ${BOOST_GRAPH_SRC_DIR}/read_graphviz_new.cpp)
add_library(boost_program_options STATIC
  ${BOOST_PROGRAM_OPTIONS_SRC_DIR}/cmdline.cpp
  ${BOOST_PROGRAM_OPTIONS_SRC_DIR}/config_file.cpp
  ${BOOST_PROGRAM_OPTIONS_SRC_DIR}/convert.cpp
  ${BOOST_PROGRAM_OPTIONS_SRC_DIR}/options_description.cpp
  ${BOOST_PROGRAM_OPTIONS_SRC_DIR}/parsers.cpp
  ${BOOST_PROGRAM_OPTIONS_SRC_DIR}/positional_options.cpp
  ${BOOST_PROGRAM_OPTIONS_SRC_DIR}/split.cpp
  ${BOOST_PROGRAM_OPTIONS_SRC_DIR}/utf8_codecvt_facet.cpp
  ${BOOST_PROGRAM_OPTIONS_SRC_DIR}/value_semantic.cpp
  ${BOOST_PROGRAM_OPTIONS_SRC_DIR}/variables_map.cpp
  ${BOOST_PROGRAM_OPTIONS_SRC_DIR}/winmain.cpp)
add_library(boost_thread STATIC
  #${BOOST_THREAD_SRC_DIR}/win32/tss_dll.cpp
  #${BOOST_THREAD_SRC_DIR}/win32/tss_pe.cpp
  #${BOOST_THREAD_SRC_DIR}/win32/thread.cpp
  ${BOOST_THREAD_SRC_DIR}/future.cpp
  ${BOOST_THREAD_SRC_DIR}/tss_null.cpp
  ${BOOST_THREAD_SRC_DIR}/pthread/once_atomic.cpp
  ${BOOST_THREAD_SRC_DIR}/pthread/once.cpp
  ${BOOST_THREAD_SRC_DIR}/pthread/thread.cpp)
add_library(boost_chrono STATIC
  ${BOOST_CHRONO_SRC_DIR}/chrono.cpp
  ${BOOST_CHRONO_SRC_DIR}/process_cpu_clocks.cpp
  ${BOOST_CHRONO_SRC_DIR}/thread_clock.cpp)
add_library(boost_system STATIC
  ${BOOST_SYSTEM_SRC_DIR}/error_code.cpp)
add_library(boost_test STATIC
  ${BOOST_TEST_SRC_DIR}/compiler_log_formatter.cpp
  #${BOOST_TEST_SRC_DIR}/cpp_main.cpp
  ${BOOST_TEST_SRC_DIR}/debug.cpp
  ${BOOST_TEST_SRC_DIR}/decorator.cpp
  ${BOOST_TEST_SRC_DIR}/execution_monitor.cpp
  ${BOOST_TEST_SRC_DIR}/framework.cpp
  ${BOOST_TEST_SRC_DIR}/junit_log_formatter.cpp
  ${BOOST_TEST_SRC_DIR}/plain_report_formatter.cpp
  ${BOOST_TEST_SRC_DIR}/progress_monitor.cpp
  ${BOOST_TEST_SRC_DIR}/results_collector.cpp
  ${BOOST_TEST_SRC_DIR}/results_reporter.cpp
  ${BOOST_TEST_SRC_DIR}/test_main.cpp
  ${BOOST_TEST_SRC_DIR}/test_tools.cpp
  ${BOOST_TEST_SRC_DIR}/test_tree.cpp
  ${BOOST_TEST_SRC_DIR}/unit_test_log.cpp
  ${BOOST_TEST_SRC_DIR}/unit_test_main.cpp
  ${BOOST_TEST_SRC_DIR}/unit_test_monitor.cpp
  ${BOOST_TEST_SRC_DIR}/unit_test_parameters.cpp
  ${BOOST_TEST_SRC_DIR}/xml_log_formatter.cpp
  ${BOOST_TEST_SRC_DIR}/xml_report_formatter.cpp)
file(GLOB SRC_FILES ${BOOST_RANDOM_SRC_DIR}/*.cpp)
add_library(boost_random STATIC ${SRC_FILES})
file(GLOB SRC_FILES ${BOOST_FILESYSTEM_SRC_DIR}/*.cpp)
add_library(boost_filesystem STATIC ${SRC_FILES})
file(GLOB SRC_FILES ${BOOST_ATOMIC_SRC_DIR}/*.cpp)
add_library(boost_atomic STATIC ${SRC_FILES})
file(GLOB SRC_FILES ${BOOST_REGEX_SRC_DIR}/*.cpp)
add_library(boost_regex STATIC ${SRC_FILES})
add_library(boost_date_time INTERFACE)
set(Boost_GRAPH_LIBRARY boost_graph)
set(Boost_PROGRAM_OPTIONS_LIBRARY boost_program_options)
set(Boost_THREAD_LIBRARY boost_thread)
set(Boost_CHRONO_LIBRARY boost_chrono)
set(Boost_SYSTEM_LIBRARY boost_system)
set(Boost_TEST_LIBRARY boost_test)
set(Boost_RANDOM_LIBRARY boost_random)
set(Boost_FILESYSTEM_LIBRARY boost_filesystem)
set(Boost_ATOMIC_LIBRARY boost_atomic)
set(Boost_REGEX_LIBRARY boost_regex)
set(Boost_DATE_TIME_LIBRARY boost_date_time)
target_include_directories(boost_graph PUBLIC ${Boost_INCLUDE_DIR})
target_include_directories(boost_program_options PUBLIC ${Boost_INCLUDE_DIR})
target_include_directories(boost_thread PUBLIC ${Boost_INCLUDE_DIR})
target_include_directories(boost_chrono PUBLIC ${Boost_INCLUDE_DIR})
target_include_directories(boost_system PUBLIC ${Boost_INCLUDE_DIR})
target_include_directories(boost_test PUBLIC ${Boost_INCLUDE_DIR})
target_include_directories(boost_random PUBLIC ${Boost_INCLUDE_DIR})
target_include_directories(boost_filesystem PUBLIC ${Boost_INCLUDE_DIR})
target_include_directories(boost_atomic PUBLIC ${Boost_INCLUDE_DIR})
target_include_directories(boost_regex PUBLIC ${Boost_INCLUDE_DIR})
target_include_directories(boost_date_time INTERFACE ${Boost_INCLUDE_DIR})
set(Boost_LIBRARIES 
  ${BOOST_GRAPH_LIBRARY}
  ${Boost_PROGRAM_OPTIONS_LIBRARY}
  ${Boost_THREAD_LIBRARY}
  ${Boost_CHRONO_LIBRARY}
  ${Boost_SYSTEM_LIBRARY}
  ${Boost_TEST_LIBRARY}
  CACHE INTERNAL "Boost libraries")
set(Boost_FOUND 1)
set(Boost_VERSION 106400)
set(Boost_MAJOR_VERSION 1)
set(Boost_MINOR_VERSION 64)
set(Boost_SUBMINOR_VERSION 0)
message("BOOST_ROOT: ${BOOST_ROOT}")
message("BOOST_INCLUDE_DIR: ${Boost_INCLUDE_DIR}")

# Add json
set(JSON_BuildTests OFF CACHE BOOL "Don't build JSON tests" FORCE)
add_subdirectory(json)

# Conditionally add curl
if(USE_CURL)
  set(CMAKE_DEBUG_POSTFIX "" CACHE STRING "Override CMAKE_DEBUG_POSTFIX, which curl sets to '-d'")
  set(BUILD_TESTING OFF CACHE BOOL "Don't build curl tests" FORCE)
  set(BUILD_CURL_EXE OFF CACHE BOOL "Don't build curl executables" FORCE)
  set(CURL_STATICLIB ON CACHE BOOL "Build the curl static library" FORCE)
  set(CURL_DISABLE_LDAP ON CACHE BOOL "Disable ldap" FORCE)
  set(CURL_CA_FALLBACK ON CACHE BOOL "Use built-in CA" FORCE)
  set(CURL_INSTALL OFF CACHE BOOL "Don't allow cURL to install" FORCE)
  # Android does not support fsetxattr
  if(ANDROID)
    set(HAVE_FSETXATTR OFF CACHE BOOL "We do not have fsetxattr" FORCE)
    set(HAVE_GLIBC_STRERROR_R OFF CACHE BOOL "We do not have glibc strerror" FORCE)
    set(HAVE_GLIBC_STRERROR_R__TRYRUN_OUTPUT "" CACHE STRING "Force the strerror output" FORCE)
    set(HAVE_POSIX_STRERROR_R ON CACHE BOOL "We do have posix strerror" FORCE)
    set(HAVE_POSIX_STRERROR_R__TRYRUN_OUTPUT "" CACHE STRING "Force the posix strerror output" FORCE)
    set(HAVE_POLL_FINE_EXITCODE "0" CACHE STRING "Force poll fine exit code" FORCE)
  endif()
  add_subdirectory(curl EXCLUDE_FROM_ALL)
endif()

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
