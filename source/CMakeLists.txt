set(SOURCE_FILES
  Client.cpp
  CachingClient.h
  CachingClient.cpp
  Request.cpp
  RequestImplementation.cpp
  ClientNSURLSession.h
  ClientNSURLSession.mm
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
  CacheLocationApple.mm
  CacheLocationWindows.cpp
  ClientModifierImplementation.h
  ClientModifierImplementation.cpp
  RequestImplementation.h
  ClientMultiRequestImplementation.h
  ClientMultiRequestImplementation.cpp
  NFHTTP.cpp)

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
  list(APPEND LINK_LIBRARIES libcurl)
  set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -lcurl")
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
