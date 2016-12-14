# -*- mode: Python; tab-width: 4; indent-tabs-mode: nil; -*-
# ex: set tabstop=4 :
# Please do not change the lines above. See PEP 8, PEP 263.

import unittest
import phone_rule_engine
from unittest.mock import Mock

class TestOperations(unittest.TestCase):

    def setUp(self):
        self.redis = Mock()
        self.testee = phone_rule_engine.RuleOperations(self.redis)

    def test_prefix_normalization(self):
        self.assertEqual(
            "40",
            self.testee._prefix("+40")
        )

    def test_prefix_validation(self):
        with self.assertRaises(ValueError):
            self.testee._prefix("40foo")

    def test_rule_validation(self):
        with self.assertRaises(ValueError):
            self.testee._rule("foobar")

    def test_rule_normalization(self):
        self.assertEqual(
            "allow",
            self.testee._rule("ALLOW")
        )

    def _mock_redis(self, response):
        self.redis.register_script = lambda script: lambda keys, args: response

    def test_invalid_redis_response(self):
        self._mock_redis(b"foobar")
        with self.assertRaises(ValueError):
            self.testee.query_rule("+407")

    def test_redis_valid(self):
        self._mock_redis(b"allow")
        self.assertTrue(
            self.testee.query_rule("+407")
        )
        self._mock_redis(b"restrict")
        self.assertFalse(
            self.testee.query_rule("+407")
        )
        self._mock_redis(None)
        self.assertIsNone(
            self.testee.query_rule("+407")
        )
