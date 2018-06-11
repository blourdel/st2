# coding=utf-8
# Licensed to the StackStorm, Inc ('StackStorm') under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import
import os
import shutil
import warnings

import six
import unittest2

from st2client.config_parser import CLIConfigParser
from st2client.config_parser import CONFIG_DEFAULT_VALUES

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE_PATH_FULL = os.path.join(BASE_DIR, '../fixtures/st2rc.full.ini')
CONFIG_FILE_PATH_PARTIAL = os.path.join(BASE_DIR, '../fixtures/st2rc.partial.ini')
CONFIG_FILE_PATH_UNICODE = os.path.join(BASE_DIR, '../fixtures/test_unicode.ini')


class CLIConfigParserTestCase(unittest2.TestCase):
    def test_constructor(self):
        parser = CLIConfigParser(config_file_path='doesnotexist', validate_config_exists=False)
        self.assertTrue(parser)

        self.assertRaises(ValueError, CLIConfigParser, config_file_path='doestnotexist',
                          validate_config_exists=True)

    def test_fix_permssions_on_existing_config(self):
        TEMP_FILE_PATH = os.path.join('st2config', '.st2', 'config')
        TEMP_CONFIG_DIR = os.path.dirname(TEMP_FILE_PATH)

        self.assertFalse(os.path.exists(TEMP_CONFIG_DIR))

        try:
            os.makedirs(TEMP_CONFIG_DIR)

            shutil.copyfile(CONFIG_FILE_PATH_FULL, TEMP_FILE_PATH)

            self.assertNotEqual(os.stat(TEMP_FILE_PATH).st_mode & 0o777, 0o770)

            parser = CLIConfigParser(config_file_path=TEMP_FILE_PATH, validate_config_exists=True)

            with warnings.catch_warnings(record=True) as warnings_list:
                result = parser.parse()

                self.assertEquals(
                    "Setting StackStorm config directory permissions ({}) to 0770".format(TEMP_CONFIG_DIR),
                    str(warnings_list[0].message))

                self.assertEqual(
                    "Setting StackStorm config file permissions ({}) to 0660".format(TEMP_FILE_PATH),
                    str(warnings_list[1].message))

            self.assertTrue(os.path.exists(TEMP_FILE_PATH))
            self.assertEqual(os.stat(TEMP_FILE_PATH).st_mode & 0o777, 0o660)

            self.assertTrue(os.path.exists(TEMP_CONFIG_DIR))
            self.assertEqual(os.stat(TEMP_CONFIG_DIR).st_mode & 0o777, 0o770)
        finally:
            if os.path.exists(TEMP_FILE_PATH):
                os.remove(TEMP_FILE_PATH)
                os.removedirs(TEMP_CONFIG_DIR)

            self.assertFalse(os.path.exists(TEMP_FILE_PATH))

    def test_parse(self):
        # File doesn't exist
        parser = CLIConfigParser(config_file_path='doesnotexist', validate_config_exists=False)
        result = parser.parse()

        self.assertEqual(CONFIG_DEFAULT_VALUES, result)

        # File exists - all the options specified
        expected = {
            'general': {
                'base_url': 'http://127.0.0.1',
                'api_version': 'v1',
                'cacert': 'cacartpath',
                'silence_ssl_warnings': False
            },
            'cli': {
                'debug': True,
                'cache_token': False,
                'timezone': 'UTC'
            },
            'credentials': {
                'username': 'test1',
                'password': 'test1',
                'api_key': None
            },
            'api': {
                'url': 'http://127.0.0.1:9101/v1'
            },
            'auth': {
                'url': 'http://127.0.0.1:9100/'
            },
            'stream': {
                'url': 'http://127.0.0.1:9102/v1/stream'
            }
        }
        parser = CLIConfigParser(config_file_path=CONFIG_FILE_PATH_FULL,
                                 validate_config_exists=False)
        result = parser.parse()
        self.assertEqual(expected, result)

        # File exists - missing options, test defaults
        parser = CLIConfigParser(config_file_path=CONFIG_FILE_PATH_PARTIAL,
                                 validate_config_exists=False)
        result = parser.parse()
        self.assertTrue(result['cli']['cache_token'], True)

    def test_get_config_for_unicode_char(self):
        parser = CLIConfigParser(config_file_path=CONFIG_FILE_PATH_UNICODE,
                                 validate_config_exists=False)
        config = parser.parse()

        if six.PY3:
            self.assertEqual(config['credentials']['password'], '密码')
        else:
            self.assertEqual(config['credentials']['password'], u'\u5bc6\u7801')
