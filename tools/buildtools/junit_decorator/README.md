# JUnit Decorator

The `decorator.py` script decorates any Unittest/TA Junit file with ownership
metadata such as feature, squad etc.

## Usage

This script is expected to be called as soon as the Junit file is ready.

```
$ python decorator.py --help
usage: decorator.py [-h] -t FILE -s FILE [-j FILE] [--test-type TEST_TYPE]
                    [--test-phase TEST_PHASE]
                    JUNIT_XML

Decorates junit.xml report with additional Spotify metadata such as feature
names and ownership. The decorated xml content is printed to STDOUT.

positional arguments:
  JUNIT_XML             Junit XML report to be decorated

optional arguments:
  -h, --help            show this help message and exit
  -t FILE, --testsuite-feature-map FILE
                        File containing a mapping between testsuites and
                        corresponding features (both XML and JSON are
                        supported)
  -s FILE, --feature-squad-map FILE
                        File containing a mapping between features and squads
                        that own them (both XML and JSON are supported)
  -j FILE, --feature-jira-feature-map FILE
                        File containing a mapping between features and Jira feature
                        (not required)
  --test-type TEST_TYPE
                        Type of the test: unittests, ta, supa
  --test-phase TEST_PHASE
                        Phase of the tests being run: premerge, push
```

## Metadata examples
See samples folder
