# Continuous Integration
Every pull request and merge to master trigger a set of [TeamCity](https://teamcity.spotify.net/) builds. See [bridge.json](../buildconf/bridge.json) for a complete list of builds. 

## CI Build Scripts
Each TeamCity build is configured to run one of the scripts in this directory, sometimes with additional command line arguments. See the individual TeamCity build configurations to view or edit the exact build pipeline commands. In general, each platform has a shell script that acts as an entry point (e.g. [osx.sh](osx.sh)) and invokes the appropriate python script (e.g. [osx.py](osx.py)). All of the platform-specific python scripts create build objects derived from [nfbuild.py](nfbuild.py). Some of the methods in the `NFBuild` python class are overriden for platform-specific functionality in the other `nfbuild*.py` files. 

## Using CI Scripts Locally
The ci scripts can be used to download dependencies, generate build files with CMake, compile targets, and run tests in local build environments as well.

On OS X, the following commands may be useful. They all assume you have already cloned the project and all of its submodules.  

### Build-in Help

For a full-list of supported cmdline command, enter:

```
sh ci/osx.sh --help
```

### Running the linter
This will flag any style errors in python and CMake files, and edit C++ source files in place. It will not compile or run any targets. 
```
sh ci/osx.sh lint
```

### Running integration tests
This will run the integration tests locally.
If you want to skip project generation, add `-generateProject=0`.
This command will not destroy the contents of your `cpp/build` folder.
```
sh ci/osx.sh local_it
``` 

### Custom builds
The CI scripts allow enabling/disabling any step of the build process.
Options groups (or workflows) are specified without a preceding dash, and will activate a group of build steps.
Additionally individual build steps can be turned on or off. For example, the command below runs the address sanitizer
without wiping the build directory:
```
sh ci/osx.sh address_sanitizer -makeBuildDirectory=0
```

New build options can be added to the ci script by calling `buildOptions.addOption(optionName, optionHelpDescription)`.

New workflows can be added by calling `buildOptions.addWorkflow(workflow_name, workflow_help_description, array_of_optionName)`.

By convention, options should be in camel case, while workflows should use underscores.