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
#if __APPLE__

#include "ClientNSURLSession.h"

#include <NFHTTP/ResponseImplementation.h>

#include <unordered_map>

#include "RequestTokenDelegate.h"
#include "RequestTokenImplementation.h"

#import <Foundation/Foundation.h>

namespace nativeformat {
namespace http {

static NSString *languageHeaderValue();
static NSString *generateLanguageHeaderValue();

class ClientNSURLSession
    : public Client,
      public RequestTokenDelegate,
      public std::enable_shared_from_this<ClientNSURLSession> {
public:
  ClientNSURLSession();
  virtual ~ClientNSURLSession();

  // Client
  std::shared_ptr<RequestToken> performRequest(
      const std::shared_ptr<Request> &request,
      std::function<void(const std::shared_ptr<Response> &)> callback) override;

  // RequestTokenDelegate
  void requestTokenDidCancel(
      const std::shared_ptr<RequestToken> &request_token) override;

private:
  static NSURLRequest *
  requestFromRequest(const std::shared_ptr<Request> &request);
  static const std::shared_ptr<Response>
  responseFromResponse(NSHTTPURLResponse *response,
                       const std::shared_ptr<Request> request, NSData *data);

  NSURLSession *_session;
  std::unordered_map<std::shared_ptr<RequestToken>, NSURLSessionTask *> _tokens;
  std::mutex _tokens_mutex;
};

ClientNSURLSession::ClientNSURLSession()
    : _session([NSURLSession
          sessionWithConfiguration:
              [NSURLSessionConfiguration defaultSessionConfiguration]]) {}

ClientNSURLSession::~ClientNSURLSession() {
  std::lock_guard<std::mutex> lock(_tokens_mutex);
  for (auto &token_task : _tokens) {
    [token_task.second cancel];
  }
  [_session invalidateAndCancel];
}

std::shared_ptr<RequestToken> ClientNSURLSession::performRequest(
    const std::shared_ptr<Request> &request,
    std::function<void(const std::shared_ptr<Response> &)> callback) {
  @autoreleasepool {
    NSURLRequest *urlRequest = requestFromRequest(request);
    const std::shared_ptr<Request> copied_request = request;
    std::shared_ptr<RequestToken> request_token =
        std::make_shared<RequestTokenImplementation>(shared_from_this(),
                                                     request->hash());
    NSURLSessionTask *task = [_session
        dataTaskWithRequest:urlRequest
          completionHandler:^(NSData *data, NSURLResponse *response,
                              NSError *error) {
            {
              std::lock_guard<std::mutex> lock(_tokens_mutex);
              _tokens.erase(request_token);
            }
            if ([response isKindOfClass:[NSHTTPURLResponse class]]) {
              callback(responseFromResponse((NSHTTPURLResponse *)response,
                                            copied_request, data));
            } else {
              callback(responseFromResponse(nil, copied_request, data));
            }
          }];
    {
      std::lock_guard<std::mutex> lock(_tokens_mutex);
      _tokens[request_token] = task;
    }
    [task resume];
    return request_token;
  }
}

void ClientNSURLSession::requestTokenDidCancel(
    const std::shared_ptr<RequestToken> &request_token) {
  std::lock_guard<std::mutex> lock(_tokens_mutex);
  [_tokens[request_token] cancel];
}

NSURLRequest *ClientNSURLSession::requestFromRequest(
    const std::shared_ptr<Request> &request) {
  static NSString *const AcceptLanguageHeader = @"Accept-Language";

  NSString *urlString = [NSString stringWithUTF8String:request->url().c_str()];
  NSURL *url = [NSURL URLWithString:urlString];
  NSMutableURLRequest *mutableRequest =
      [NSMutableURLRequest requestWithURL:url
                              cachePolicy:NSURLRequestReloadIgnoringCacheData
                          timeoutInterval:30.0];
  mutableRequest.HTTPMethod =
      [NSString stringWithUTF8String:request->method().c_str()];
  for (const auto &header : request->headerMap()) {
    [mutableRequest
                  addValue:[NSString stringWithUTF8String:header.second.c_str()]
        forHTTPHeaderField:[NSString
                               stringWithUTF8String:header.first.c_str()]];
  }
  size_t data_length = 0;
  const unsigned char *data = request->data(data_length);
  if (data_length > 0) {
    mutableRequest.HTTPBody = [NSData dataWithBytes:data length:data_length];
  }
  if (!mutableRequest.allHTTPHeaderFields[AcceptLanguageHeader]) {
    [mutableRequest setValue:languageHeaderValue()
          forHTTPHeaderField:AcceptLanguageHeader];
  }
  return mutableRequest.copy;
}

const std::shared_ptr<Response>
ClientNSURLSession::responseFromResponse(NSHTTPURLResponse *response,
                                         const std::shared_ptr<Request> request,
                                         NSData *data) {
  std::shared_ptr<Response> new_response =
      std::make_shared<ResponseImplementation>(
          request, (const unsigned char *)data.bytes, data.length,
          (StatusCode)response.statusCode, false);
  for (NSString *header in response.allHeaderFields.allKeys) {
    (*new_response)[header.UTF8String] =
        [response.allHeaderFields[header] UTF8String];
  }
  return new_response;
}

// Lifted from
// https://raw.githubusercontent.com/spotify/SPTDataLoader/master/SPTDataLoader/SPTDataLoaderRequest.m

static NSString *generateLanguageHeaderValue() {
  const NSInteger SPTDataLoaderRequestMaximumLanguages = 2;
  NSString *const SPTDataLoaderRequestEnglishLanguageValue = @"en";
  NSString *const SPTDataLoaderRequestLanguageHeaderValuesJoiner = @", ";

  NSString * (^constructLanguageHeaderValue)(NSString *, double) =
      ^NSString *(NSString *language, double languageImportance) {
    NSString *const SPTDataLoaderRequestLanguageFormatString = @"%@;q=%.2f";
    return [NSString stringWithFormat:SPTDataLoaderRequestLanguageFormatString,
                                      language, languageImportance];
  };

  NSArray *languages = [NSBundle mainBundle].preferredLocalizations;
  if (languages.count > SPTDataLoaderRequestMaximumLanguages) {
    languages = [languages
        subarrayWithRange:NSMakeRange(0, SPTDataLoaderRequestMaximumLanguages)];
  }
  double languageImportanceCounter = 1.0;
  NSMutableArray *languageHeaderValues =
      [NSMutableArray arrayWithCapacity:languages.count];
  BOOL containsEnglish = NO;
  for (NSString *language in languages) {
    if (!containsEnglish) {
      NSString *const SPTDataLoaderRequestLanguageLocaleSeparator = @"-";
      NSString *languageValue =
          [language componentsSeparatedByString:
                        SPTDataLoaderRequestLanguageLocaleSeparator]
              .firstObject;
      if ([languageValue
              isEqualToString:SPTDataLoaderRequestEnglishLanguageValue]) {
        containsEnglish = YES;
      }
    }

    if (languageImportanceCounter == 1.0) {
      [languageHeaderValues addObject:language];
    } else {
      [languageHeaderValues addObject:constructLanguageHeaderValue(
                                          language, languageImportanceCounter)];
    }
    languageImportanceCounter -= (1.0 / languages.count);
  }
  if (!containsEnglish) {
    [languageHeaderValues
        addObject:constructLanguageHeaderValue(
                      SPTDataLoaderRequestEnglishLanguageValue, 0.01)];
  }
  return [languageHeaderValues
      componentsJoinedByString:SPTDataLoaderRequestLanguageHeaderValuesJoiner];
}

static NSString *languageHeaderValue() {
  static NSString *languageHeaderValue = nil;
  static dispatch_once_t onceToken;
  dispatch_once(&onceToken, ^{
    languageHeaderValue = generateLanguageHeaderValue();
  });
  return languageHeaderValue;
}

std::shared_ptr<Client> createNSURLSessionClient() {
  return std::make_shared<ClientNSURLSession>();
}

} // namespace http
} // namespace nativeformat

#endif
