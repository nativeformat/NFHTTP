# -*- coding: utf-8 -*-
# Copyright (c) 2016 Spotify AB

import os
import os.path
import json
import unittest
from shutil import copyfile
from mention_bot import write_mentionbot_with_service_info_files as writer


class MentionBotTest(unittest.TestCase):
    MENTIONBOT_FILE = '.mention-bot'

    def setUp(self):
        # work from fixtures directory
        self.prev_wd = os.getcwd()
        os.chdir(os.path.join(os.path.dirname(__file__), 'fixtures/service_info'))

    def tearDown(self):
        os.remove(self.MENTIONBOT_FILE)
        os.chdir(self.prev_wd)

    def prepare_mb_with_fixture(self, filename):
        if filename:
            filename = os.path.join('../mb', filename)
            copyfile(filename, self.MENTIONBOT_FILE)
        elif os.path.isfile(self.MENTIONBOT_FILE):
            os.remove(self.MENTIONBOT_FILE)
        return self.MENTIONBOT_FILE

    def test_updates_without_pre_data(self):
        # Arrange
        self.prepare_mb_with_fixture('mention-bot-without-data.json')
        infos = ['valid/valid_service_info_2.yaml']

        # Act
        writer(infos)

        # Assert
        with open(self.MENTIONBOT_FILE, mode="r") as stream:
            final_mention_bot = json.load(stream)
            self.assertEqual(1, len(final_mention_bot.keys()))
            self.assertTrue("alwaysNotifyForPaths" in final_mention_bot)
            self.assertEqual(3, len(final_mention_bot.get("alwaysNotifyForPaths")))
            self.assertEqual(u'dan', final_mention_bot.get("alwaysNotifyForPaths")[0]['name'])
            self.assertEqual(['valid/app/*.java'], final_mention_bot.get("alwaysNotifyForPaths")[0]['files'])
            self.assertEqual(u'brannvall', final_mention_bot.get("alwaysNotifyForPaths")[1]['name'])
            self.assertEqual(['valid/app/*.java'], final_mention_bot.get("alwaysNotifyForPaths")[1]['files'])
            self.assertEqual(u'menny', final_mention_bot.get("alwaysNotifyForPaths")[2]['name'])
            self.assertEqual(['valid/app/*.java'], final_mention_bot.get("alwaysNotifyForPaths")[2]['files'])

    def test_updates_without_facts_section(self):
        # Arrange
        self.prepare_mb_with_fixture('mention-bot-without-data.json')
        infos = ['valid/valid_service_info_without_facts.yaml']

        # Act
        writer(infos)

        # Assert
        with open(self.MENTIONBOT_FILE, mode="r") as stream:
            final_mention_bot = json.load(stream)
            self.assertEqual(0, len(final_mention_bot.keys()))

    def test_updates_without_mentionbot_section(self):
        # Arrange
        self.prepare_mb_with_fixture('mention-bot-without-data.json')
        infos = ['valid/valid_service_info_without_mention_bot.yaml']

        # Act
        writer(infos)

        # Assert
        with open(self.MENTIONBOT_FILE, mode="r") as stream:
            final_mention_bot = json.load(stream)
            self.assertEqual(0, len(final_mention_bot.keys()))

    def test_updates_when_mention_bot_file_does_not_exist(self):
        # Arrange
        self.prepare_mb_with_fixture(None)
        infos = ['valid/valid_service_info_2.yaml']

        # Act
        writer(infos)

        # Assert
        with open(self.MENTIONBOT_FILE, mode="r") as stream:
            final_mention_bot = json.load(stream)
            self.assertEqual(1, len(final_mention_bot.keys()))
            self.assertTrue("alwaysNotifyForPaths" in final_mention_bot)
            self.assertEqual(3, len(final_mention_bot.get("alwaysNotifyForPaths")))
            self.assertEqual(u'dan', final_mention_bot.get("alwaysNotifyForPaths")[0]['name'])
            self.assertEqual(['valid/app/*.java'], final_mention_bot.get("alwaysNotifyForPaths")[0]['files'])
            self.assertEqual(u'brannvall', final_mention_bot.get("alwaysNotifyForPaths")[1]['name'])
            self.assertEqual(['valid/app/*.java'], final_mention_bot.get("alwaysNotifyForPaths")[1]['files'])
            self.assertEqual(u'menny', final_mention_bot.get("alwaysNotifyForPaths")[2]['name'])
            self.assertEqual(['valid/app/*.java'], final_mention_bot.get("alwaysNotifyForPaths")[2]['files'])

    def test_updates_files_with_root_service_info(self):
        # Arrange
        self.prepare_mb_with_fixture(None)
        infos = ['valid_service_info_1.yaml']

        # Act
        writer(infos)

        # Assert
        with open(self.MENTIONBOT_FILE, mode="r") as stream:
            final_mention_bot = json.load(stream)
            self.assertEqual(['*', 'app/*.java'], final_mention_bot.get("alwaysNotifyForPaths")[0]['files'])

    def test_updates_with_blacklist(self):
        # Arrange
        self.prepare_mb_with_fixture('mention-bot-with-blacklist.json')
        infos = ['valid_service_info_1.yaml']

        # Act
        writer(infos)

        # Assert
        with open(self.MENTIONBOT_FILE, mode="r") as stream:
            final_mention_bot = json.load(stream)
            self.assertEqual(2, len(final_mention_bot.keys()))
            self.assertTrue("alwaysNotifyForPaths" in final_mention_bot)
            self.assertTrue("userBlacklist" in final_mention_bot)
            self.assertEqual(6, len(final_mention_bot.get("userBlacklist")))
            self.assertEqual(["bchristensen", "sergey", "johboh", "marcusfs", "madis", "hellman"],
                             final_mention_bot.get("userBlacklist"))

    def test_updates_without_pre_data_with_multiple_paths(self):
        # Arrange
        self.prepare_mb_with_fixture('mention-bot-without-data.json')
        infos = ['valid/valid_service_info_2_with_multiple_paths.yaml']

        # Act
        writer(infos)

        # Assert
        with open(self.MENTIONBOT_FILE, mode="r") as stream:
            final_mention_bot = json.load(stream)
            self.assertEqual(1, len(final_mention_bot.keys()))
            self.assertTrue("alwaysNotifyForPaths" in final_mention_bot)
            self.assertEqual(3, len(final_mention_bot.get("alwaysNotifyForPaths")))
            self.assertEqual(u'dan', final_mention_bot.get("alwaysNotifyForPaths")[0]['name'])
            self.assertEqual(['valid/app/*.java', 'valid/app/spotlets/radio/**/*.java'], final_mention_bot.get("alwaysNotifyForPaths")[0]['files'])
            self.assertEqual(u'brannvall', final_mention_bot.get("alwaysNotifyForPaths")[1]['name'])
            self.assertEqual(['valid/app/*.java', 'valid/app/spotlets/radio/**/*.java'], final_mention_bot.get("alwaysNotifyForPaths")[1]['files'])
            self.assertEqual(u'menny', final_mention_bot.get("alwaysNotifyForPaths")[2]['name'])
            self.assertEqual(['valid/app/*.java', 'valid/app/spotlets/radio/**/*.java'], final_mention_bot.get("alwaysNotifyForPaths")[2]['files'])
