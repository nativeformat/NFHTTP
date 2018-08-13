<img alt="NFHTTP" src="NFHTTP.png" width="100%" max-width="888">

[![CircleCI](https://circleci.com/gh/spotify/NFHTTP.svg?style=svg)](https://circleci.com/gh/spotify/NFHTTP)
[![License](https://img.shields.io/github/license/spotify/NFHTTP.svg)](LICENSE)
[![Spotify FOSS Slack](https://slackin.spotify.com/badge.svg)](https://slackin.spotify.com)
[![Readme Score](http://readme-score-api.herokuapp.com/score.svg?url=https://github.com/spotify/nfhttp)](http://clayallsopp.github.io/readme-score?url=https://github.com/spotify/nfhttp)

A cross platform C++ HTTP framework. 

- [x] 📱 [iOS](https://www.apple.com/ios/) 9.0+
- [x] 💻 [OS X](https://www.apple.com/macos/) 10.11+
- [x] 🐧 [Ubuntu](https://www.ubuntu.com/) Trusty 14.04+
- [x] 🤖 [Android](https://developer.android.com/studio/) SDK r24+
- [x] 🖥️ [Microsoft UWP](https://developer.microsoft.com/en-us/windows/apps)

## Architecture :triangular_ruler:
`NFHTTP` is designed as a common C++ interface to communicate with different systems over HTTP! The API allows you to create objects to make `Requests` and read `Responses`. 
To initiate, send and receive messages you create and use a `Client` object.

## Installation :inbox_tray:
`NFHTTP` is a [Cmake](https://cmake.org/) project, while you are free to download the prebuilt static libraries it is recommended to use Cmake to install this project into your wider project. In order to add this into a wider Cmake project (who needs monorepos anyway?), simply add the following line to your `CMakeLists.txt` file:
```
add_subdirectory(NFHTTP)
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
The API is rather small. To implement request/response you
1. Create a `Client`.
2. Create a `Request`.
3. Create a `Response` callback if needed.
4. Use `Client` to send your request and receive your response!

To see this in action, look at `NFHTTPCLI.cpp`.

## Contributing :mailbox_with_mail:
Contributions are welcomed, have a look at the [CONTRIBUTING.md](CONTRIBUTING.md) document for more information.

## License :memo:
The project is available under the [Apache 2.0](http://www.apache.org/licenses/LICENSE-2.0) license.

### Acknowledgements
- None yet. Maybe it'll be you!
