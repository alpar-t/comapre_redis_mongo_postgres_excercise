# -*- mode: Python; tab-width: 4; indent-tabs-mode: nil; -*-
# ex: set tabstop=4 :
# Please do not change the lines above. See PEP 8, PEP 263.
""" Provide a generic Lua testing test case  """

import unittest
import redis
import os
from uuid import uuid4
from functools import lru_cache

from phone_rule_engine  import RuleOperations


class LuaTestCase(unittest.TestCase):
    """ Implements a descriptive test for Lua scripts

        Provides a convenient way to describe a test, takes care of talking
        with redis, loading the script, checking results and isolates the
        testcaes so that data loaded by previus test cases do not affect lather
        ones.
    """

    def setUp(self):
        self.redis = redis.StrictRedis(
            host='localhost', port=os.environ.get("REDIS_PORT", "6379"), db=0
        )
        self.rule_op = RuleOperations(self.redis, str(uuid4()))
        self.defaultGiven = {
            "rules": {},
            "rules:org": {},
            "rules:trial": {}
        }
        self.test_org_id = "some-test-org-id"

    @lru_cache()
    def load_script(self, path):
        """ Loads the path specified in argumenta and memoizes """
        with open(path, 'r') as script:
            return script.read()

    def given(self, data):
        """ Loads data into redis """
        test_data = {}
        test_data.update(self.defaultGiven)
        test_data.update(data)
        for key, value in test_data["rules"].items():
            self.rule_op.push_generic_rule(key, value)
        for key, value in test_data["rules:trial"].items():
            self.rule_op.push_trial_rule(key, value)
        for key, value in test_data["rules:org"].items():
            self.rule_op.push_org_rule(
                key, value, self.test_org_id
            )

    def expect(self, expected):
        """ Check the expected output fo running the script """
        for each in expected:
            result = each[-1]
            args = [str(x) for x in each[:-1]]
            redis_result = self.rule_op.query_rule(*args)
            if redis_result == True:
                redis_result = "allow"
            if redis_result == False:
                redis_result = "restrict"
            self.assertEqual(
                result,
                redis_result,
                ("The expected output for {} was {} " +
                "but redis returned {}").format(
                    args, result, redis_result
                )
            )
