#!/usr/bin/python


class Teamcity:
    @staticmethod
    def testSuiteStarted(name):
        return "##teamcity[testSuiteStarted name='%s']\n" % (name)

    @staticmethod
    def testSuiteFinished(name):
        return "##teamcity[testSuiteFinished name='%s']\n" % (name)

    @staticmethod
    def testStarted(name):
        return ("##teamcity[testStarted name='%s' "
                "captureStandardOutput='true']\n") % (name)

    @staticmethod
    def testFinished(name):
        return "##teamcity[testFinished name='%s']\n" % (name)

    @staticmethod
    def testFailed(name):
        return "##teamcity[testFailed name='%s']\n" % (name)
