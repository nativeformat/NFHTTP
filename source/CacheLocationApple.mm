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

#include <NFHTTP/Client.h>

#import <Foundation/Foundation.h>

#include <sys/stat.h>

namespace nativeformat {
namespace http {

std::string standardCacheLocation()
{
    NSArray *paths = NSSearchPathForDirectoriesInDomains(NSApplicationSupportDirectory, NSUserDomainMask, YES);
    NSString *applicationSupportDirectory = [paths firstObject];
    NSString *cacheLocation = [applicationSupportDirectory stringByAppendingPathComponent:@"nfsmartplayer"];

    BOOL isDir = NO;
    NSFileManager *fileManager = [[NSFileManager alloc] init];
    if (![fileManager fileExistsAtPath:cacheLocation isDirectory:&isDir] && !isDir) {
        if (![fileManager createDirectoryAtPath:cacheLocation
                    withIntermediateDirectories:YES
                                     attributes:nil
                                          error:NULL]) {
            printf("Failed to create cache directory: %s\n", cacheLocation.UTF8String);
        }
    }
    return cacheLocation.UTF8String;
}

}  // namespace http
}  // namespace nativeformat

#endif
