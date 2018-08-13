add_library(sqlite "${CMAKE_CURRENT_SOURCE_DIR}/sqlite/sqlite3.c")
target_compile_definitions(sqlite PUBLIC -DSQLITE_THREADSAFE=2)

find_package(OpenSSL 1.0.0 REQUIRED)
find_package(Boost 1.54.0 REQUIRED)

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
