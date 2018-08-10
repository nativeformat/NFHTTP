# BuildTimeRecorder
A script that records build times on all platforms and indexes build-specific data on elasticsearch.

## Usage

Build scripts are expected to call this script twice. Once at the beginning and once at the end.

The second time you call the script you provide any information specific to this build that you would like indexed.

## Example (w/bash)
```
python build_time_recorder.py start
sleep 5
python build_time_recorder.py stop --json "{\"foo\" : \"bar\"}"
```

## Example using JSON file instead of RAW JSON
```
echo "{\"foo\" : \"bar\"}" >> hello.json
python build_time_recorder.py start
sleep 5
python build_time_recorder.py stop --file "hello.json"
```


## Example specifying temporary file location for timing data
```
python build_time_recorder.py start --timefile ".myTmpFile"
sleep 5
python build_time_recorder.py stop --timefile ".myTmpFile" --json "{\"foo\" : \"bar\"}"
```


## Example utilizing a dryrun (does not index data)
```
python build_time_recorder.py start
sleep 5
python build_time_recorder.py stop --dryrun --json "{\"foo\" : \"bar\"}"
```

## Example utilizing a async (double fork the networking stage)
```
python build_time_recorder.py start
sleep 5
python build_time_recorder.py stop --async --json "{\"foo\" : \"bar\"}"
```
## FAQ

* *Q: Is Internet required to be able to build?*
* A: No internet required to build, the script will just fail silently if you are offline. This is fine because we are just trying to get as many data points as possible and online builds will be sufficient.

* *Q: What more information is collected, apart from the build time?*
* A: Information about the build, the git commit, and some basic system info derived from `facter -j`

* *Q: What is the purpose?*
* A: To get a basic understanding of our build metrics and build behaviors and to be able to see how they change over time. For example, we in the App Development Productivity tribe would like to know the total number of minutes spent building the client per developer per day. This will be a valuable metric which we can then use to improve build times.

* *Q: Can build times be collected from Teamcity instead?*
* A: Because we are interested in developer building behavior, this information can't be collected from TeamCity.

* *Q: Is this Spyware :-P?*
* A: Not spyware :)
