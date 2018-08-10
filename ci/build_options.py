#!/usr/bin/env python

import sys
import argparse

# Argument parsing abstraction designed for the build context.
# Generates an array of buildOptions from an input arg list.
# Allows options to be grouped into workflows, and workflows
# to be overridden with minor changes.

# Example commands:

# run the lint workflow with an override to disable dependencies install:
# python build_options.py lint -installDependencies=0 -v

# run the default workflow with an override to make it fly.
# python build_options.py -doFlyAway=1 -v


class BuildOptions:

    def __init__(self):
        self.options = {}
        self.workflows = {}
        self.verbose = True

    # Define a build option, with documentation.
    def addOption(self, option, doc):
        self.options[option] = doc

    # Define a workflow, which consists of a group of build options.
    # This will be an optional single positional argument.
    def addWorkflow(self, workflow, doc, options):
        for option in options:
            if option not in self.options:
                self.flushed_print(
                    "Error: Workflow %s contains invalid option %s"
                    % (workflow, option))
                exit(1)
        self.workflows[workflow] = {
            'doc': doc,
            'options': {x: '1' for x in options}
        }

    # Define the default workflow, if the cmdline input doesn't include
    # a position workflow arg.
    def setDefaultWorkflow(self, doc, options):
        self.addWorkflow("default", doc, options)

    def getOptionDoc(self, option):
        return self.options[option]

    def getWorkflowHelp(self):
        str = ""
        for workflow, data in self.workflows.iteritems():
            str += "%s:\n\t%s\n" % (workflow, data['doc'])
        return str

    # Parse input arguments
    def parseArgs(self):
        parser = argparse.ArgumentParser(
            formatter_class=argparse.RawTextHelpFormatter)

        # Verbose is automatically defined
        parser.add_argument("-quiet", "-q",
                            help="Mute build steps",
                            action='store_true')

        # Can have any number of workflows. If 0, it runs the default workflow.
        # If more than 1, the built options get intersected
        parser.add_argument("workflows", nargs='*', default=['default'],
                            help=self.getWorkflowHelp())

        # Define build options with leading -
        for k, v in self.options.iteritems():
            parser.add_argument("-" + k, help=v)
        args = parser.parse_args()
        argHash = vars(args)
        result = {}

        if 'quiet' in argHash and argHash['quiet']:
            self.verbose = False

        for workflow in argHash['workflows']:
            if workflow not in self.workflows:
                self.flushed_print("Error: Specified invalid workflow %s" %
                                   workflow)
                exit(1)
            # Load options from selected workflows
            result.update(self.workflows[workflow]['options'])

        # Apply option overrides to workflow
        for option, doc in self.options.iteritems():
            if option in argHash and argHash[option]:
                result[option] = argHash[option]

        return [k for k, v in result.iteritems() if v == '1']

    # Print which build options are enabled.
    def verbosePrintBuildOptions(self, args):
        if self.verbose:
            self.flushed_print("Build Options: " + str(args))

    # Caller should call this when a build option is being executed
    # for verbose build logging.
    def verbosePrint(self, option):
        if self.verbose:
            self.flushed_print("===== %s =====" % self.getOptionDoc(option))

    # Check if this given build option is defined. If so, print the step has
    # begun and return true so caller can run the step.
    # Sanity check the input option to catch typos.
    def checkOption(self, args, arg, quiet=False):
        if arg not in self.options:
            self.flushed_print("Error: Checked undefined option %s" % arg)
            exit(1)
        if arg in args:
            if not quiet:
                self.verbosePrint(arg)
            return True
        return False

    def flushed_print(self, str):
        print str
        sys.stdout.flush()


# Create a toy version for testing if user executes this file directly
def test_version():

    buildOptions = BuildOptions()
    buildOptions.addOption("option1", "option 1 description")
    buildOptions.addOption("option2", "option 2 description")
    buildOptions.addOption("option3", "option 3 description")
    buildOptions.setDefaultWorkflow("Default workflow description", [
        'option1'
    ])
    buildOptions.addWorkflow("workflow1", "workflow1 description", [
        'option1',
        'option2'
    ])
    buildOptions.addWorkflow("workflow2", "workflow2 description", [
        'option2',
        'option3'
    ])

    options = buildOptions.parseArgs()
    buildOptions.verbosePrintBuildOptions(options)

    if buildOptions.checkOption(options, "option1"):
        buildOptions.flushed_print("running option1")

    if buildOptions.checkOption(options, "option2"):
        buildOptions.flushed_print("running option2")

    if buildOptions.checkOption(options, "option3"):
        buildOptions.flushed_print("running option3")


if __name__ == "__main__":
    test_version()
