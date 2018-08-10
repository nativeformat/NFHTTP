# -*- coding: utf-8 -*-
# Copyright (c) 2016 Spotify AB

import unittest
import purgatory_validate
from purgatory_validate import PurgatoryValidationException


class PurgatoryValidateTest(unittest.TestCase):

    def test_validate_successful(self):
        self.assertTrue(purgatory_validate.validate([{
            'added_at': '2016-11-14T20:48:58.172018',
            'jira': 'JIRA-123',
            'owner': 'testOwner',
            'reason': 'test reason',
            'test': 'test.Class.method'}]))

    def test_validate_missing_key_raises_exception(self):
        self.assertRaises(
            PurgatoryValidationException,
            purgatory_validate.validate, [{
                'added_at': '2016-11-14T20:48:58.172018',
                'jira': 'JIRA-123',
                'owner': 'testOwner',
                'reason': 'test reason'}])

        self.assertRaises(
            PurgatoryValidationException,
            purgatory_validate.validate, [{
                'added_at': '2016-11-14T20:48:58.172018',
                'jira': 'JIRA-123',
                'owner': 'testOwner',
                'test': 'test.Class.method'}])

        self.assertRaises(
            PurgatoryValidationException,
            purgatory_validate.validate, [{
                'added_at': '2016-11-14T20:48:58.172018',
                'jira': 'JIRA-123',
                'reason': 'test reason',
                'test': 'test.Class.method'}])

        self.assertRaises(
            PurgatoryValidationException,
            purgatory_validate.validate, [{
                'added_at': '2016-11-14T20:48:58.172018',
                'owner': 'testOwner',
                'reason': 'test reason',
                'test': 'test.Class.method'}])

        self.assertRaises(
            PurgatoryValidationException,
            purgatory_validate.validate, [{
                'jira': 'JIRA-123',
                'owner': 'testOwner',
                'reason': 'test reason',
                'test': 'test.Class.method'}])

    def test_validate_extra_key_raises_exception(self):
        self.assertRaises(
            PurgatoryValidationException,
            purgatory_validate.validate, [{
                'jira': 'JIRA-123',
                'owner': 'testOwner',
                'reason': 'test reason',
                'test': 'test.Class.method',
                'extra_key': 'extra test data'}])
