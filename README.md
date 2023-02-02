<img alt="NFHTTP" src="NFHTTP.png" width="100%" max-width="888">

[![CircleCI](https://circleci.com/gh/spotify/NFHTTP/tree/master.svg?style=svg)](https://circleci.com/gh/spotify/NFHTTP/tree/master)
[![License](https://img.shields.io/github/license/spotify/NFHTTP.svg)](LICENSE)
[![Spotify FOSS Slack](https://slackin.spotify.com/badge.svg)](https://slackin.spotify.com)
[![Readme Score](http://readme-score-api.herokuapp.com/score.svg?url=https://github.com/spotify/nfhttp)](http://clayallsopp.github.io/readme-score?url=https://github.com/spotify/nfhttp)

A cross platform C++ HTTP framework. 

- [x] 📱 [iOS](https://www.apple.com/ios/) 9.0+
- [x] 💻 [OS X](https://www.apple.com/macos/) 10.11+
- [x] 🐧 [Ubuntu](https://www.ubuntu.com/) Trusty 14.04+
- [x] 🤖 [Android](https://developer.android.com/studio/) SDK r24+
- [x] 🖥️ [Microsoft UWP](https://developer.microsoft.com/en-us/windows/apps)

Developed at Spotify 2019-2022, Discontinued and handed over to new maintainers January 2023

## Raison D'être :thought_balloon:
At Spotify we have performed studies that show the efficacy of using native backed solutions for interfacing to backends, especially when it came to the battery life of certain devices. In order to carry this forward in the cross-platform C++ world, we created this library that provides a common interface to many of the system level HTTP interfaces, and predictable caching and request hooking. We found that many of the current solutions that claimed to do this lacked key supports for many kinds of platforms, and ended up being libraries that heavily favoured 1 platform and gave the other platforms a generic implementation. We also wanted to provide a caching layer that was consistent across all platforms in our layered architecture.

## Architecture :triangular_ruler:
`NFHTTP` is designed as a common C++ interface to communicate with different systems over HTTP! The API allows you to create objects to make `Requests` and read `Responses`. To initiate, send and receive messages you create and use a `Client` object. This is a layered architecture where requests and responses can pass through multiple places in the stack and get decorated or have actions taken upon them.

The layer design is as follows:
- **The Modification layer**, which takes requests and responses, performs any modifications on them that might be required by the functions provided to the factory, and forwards them on.
- **The Multi-Request Layer**, which takes a request, determines if the same request is currently being executed, then ties the response to that request with the response currently coming in from the previously sent request.
- **The Caching Layer**, which takes a request, determines whether it is cached and if so sends a response immediately, if not forwards the request, and when it receives the response stores the response in its cache.
- **The Native Layer**, which takes a request and converts it to a system level call depending on the system the user is using, then converts the response back to an NFHTTP response and sends the response back up the chain.

Our support table looks like so:

| OS            | Underlying Framework                                                                                         | Status  |
| ------------- |:------------------------------------------------------------------------------------------------------------:| -------:|
| iOS           | [NSURLSession](https://developer.apple.com/documentation/foundation/nsurlsession)                            | Stable  |
| OSX           | [NSURLSession](https://developer.apple.com/documentation/foundation/nsurlsession)                            | Stable  |
| Linux         | [curl](https://curl.haxx.se/)                                                                                | Stable  |
| Android       | [curl](https://curl.haxx.se/)                                                                                | Beta    |
| Windows       | [WinHTTP](https://docs.microsoft.com/en-us/windows/desktop/winhttp/about-winhttp)                            | Alpha   |

In addition to this, it is also possible to use curl on any of the above platforms or boost ASIO (provided by CPP REST SDK).

## Dependencies :globe_with_meridians:
* [C++ REST SDK](https://github.com/Microsoft/cpprestsdk)
* [curl](https://curl.haxx.se/)
* [JSON for Modern C++](https://github.com/nlohmann/json)
* [OpenSSL](https://www.openssl.org/)
* [SQLite](https://www.sqlite.org/index.html)
* [boost](https://www.boost.org/)

## Installation :inbox_tray:
`NFHTTP` is a [Cmake](https://cmake.org/) project, while you are free to download the prebuilt static libraries it is recommended to use Cmake to install this project into your wider project. In order to add this into a wider Cmake project (who needs monorepos anyway?), simply add the following lines to your `CMakeLists.txt` file:
```
add_subdirectory(NFHTTP)

# Link NFHTTP to your executables or target libs
target_link_libraries(your_target_lib_or_executable NFHTTP)
```

### For iOS/OSX
Generate an [Xcode](https://developer.apple.com/xcode/) project from the Cmake project like so:
```shell
$ git submodule update --init --recursive
$ mkdir build
$ cd build
$ cmake .. -GXcode
```

### For linux
Generate a [Ninja](https://ninja-build.org/) project from the Cmake project like so:
```shell
$ git submodule update --init --recursive
$ mkdir build
$ cd build
$ cmake .. -GNinja
```

### For Android
Use [gradle](https://gradle.org/)
```
android {
    compileSdkVersion 26
    defaultConfig {
        applicationId "com.spotify.nfhttptest_android"
        minSdkVersion 19
        targetSdkVersion 26
        versionCode 1
        versionName "1.0"
        externalNativeBuild {
            cmake {
                cppFlags ""
                arguments "-DANDROID_APP=1 -DANDROID=1"
            }
        }
    }

    sourceSets {
        main {
            jniLibs.srcDirs = ['src/main/cpp']
        }
    }

    externalNativeBuild {
        cmake {
            path "../CMakeLists.txt"
        }
    }
}
```

### For Windows
Generate a [Visual Studio](https://visualstudio.microsoft.com/) project from the Cmake project like so:

```shell
$ mkdir build
$ cd build
$ cmake .. -G "Visual Studio 12 2013 Win64"
```

## Usage example :eyes:
In order to execute HTTP requests, you must first create a client like so:
```C++
auto client = nativeformat::http::createClient(nativeformat::http::standardCacheLocation(),
                                               "NFHTTP-" + nativeformat::http::version());
```

It is wise to only create one client per application instance, in reality you will only need one (unless you need to separate the caching mechanism for your own reasons). After you have done this you can proceed to creating request objects like so:
```C++
const std::string url = "http://localhost:6582/world";
auto request = nativeformat::http::createRequest(url, std::unordered_map<std::string, std::string>());
```

This will create a GET request with no added headers to send to the localhost:682/world location. This does not mean other headers will not be added, we have multiple layers that will add caching requirement headers, language headers, content size headers and the native layer can also add headers as it sees fit. After we have created our request we can then execute it:
```C++
auto token = client->performRequest(request, [](const std::shared_ptr<nativeformat::http::Response> &response) {
    printf("Received Response: %s\n", response->data());
});
```

The callback will be called asynchronously in whatever thread the native libraries post the response on, so watch out for thread safety within this callback. In order to execute requests synchronously on whatever thread you happen to be on, you can perform the follow actions:
```C++
auto response = client->performSynchronousRequest(request);
printf("Received Response: %s\n", response->data());
```

You might wonder how you can hook requests and responses, this can be done when creating the client, for example:
```C++
auto client = nativeformat::http::createClient(nativeformat::http::standardCacheLocation(),
                                               "NFHTTP-" + nativeformat::http::version(),
                                               [](std::function<void(const std::shared_ptr<nativeformat::http::Request> &request)> callback,
                                                  const std::shared_ptr<nativeformat::http::Request> &request) {
                                                 printf("Request URL: %s\n", request->url().c_str());
                                                 callback(request);
                                               },
                                               [](std::function<void(const std::shared_ptr<nativeformat::http::Response> &response, bool retry)> callback,
                                                  const std::shared_ptr<nativeformat::http::Response> &response) {
                                                 printf("Response URL: %s\n", response->request()->url().c_str());
                                                 callback(response, false);
                                               });
```

Here we have hooked the client up to receive requests and responses via the hook functions. Because we are now part of the layered architecture, we can perform any changes we want on the requests or responses, such as decorating with OAuth tokens, redirecting to other URLs, retrying responses or even cancelling responses altogether. If you are interested in the concept of cache pinning, it can be done like so:
```C++
client->pinResponse(response, "my-offlined-entity-token");
```

This will then ensure that the response is in the cache until it is explicitly removed, and ignore all backend caching directives.

## Contributing :mailbox_with_mail:
Contributions are welcomed, have a look at the [CONTRIBUTING.md](CONTRIBUTING.md) document for more information.

## License :memo:
The project is available under the [Apache 2.0](http://www.apache.org/licenses/LICENSE-2.0) license.

### Acknowledgements
- Icon in readme banner is “[Download](https://thenounproject.com/search/?q=http&i=174663)” by romzicon from the Noun Project.

#### Contributors
* [Will Sackfield](https://github.com/8W9aG)
* [Julia Cox](https://github.com/astrocox)
* [David Rubinstein](https://github.com/drubinstein)
* [Justin Sarma](https://github.com/jsarma)

