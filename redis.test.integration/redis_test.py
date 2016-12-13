# -*- mode: Python; tab-width: 4; indent-tabs-mode: nil; -*-
# ex: set tabstop=4 :
# Please do not change the lines above. See PEP 8, PEP 263.
""" Provide a generic Lua testing test case  """

import unittest
import redis
from uuid import uuid4
from functools import lru_cache


REDIS_DB = 0


class LuaTestCase(unittest.TestCase):
    """ Implements a descriptive test for Lua scripts

        Provides a convenient way to describe a test, takes care of talking
        with redis, loading the script, checking results and isolates the
        testcaes so that data loaded by previus test cases do not affect lather
        ones.
    """

    def setUp(self):
        self.redis = redis.StrictRedis(host='localhost', port=32768, db=0)
        self.defaultGiven = {
            "rules": {},
            "rules:org": {},
            "rules:trial": {}
        }
        self.uuid = "{}:".format(uuid4())

    def given(self):
        return self.defaultGiven

    def expect(self):
        return "return 'foobar'", {}

    @lru_cache()
    def load_script(self, path):
        with open(path, 'r') as script:
            return script.read()

    def test_run(self):
        test_data = {}
        test_data.update(self.defaultGiven)
        test_data.update(self.given())
        for rule in ("rules", "rules:trial"):
            for key, value in test_data[rule].items():
                self.redis.hset(self.uuid + rule, key, value)
        for key, value in test_data["rules:org"]:
            org_id, _ = key.split(":", 2)
            self.redis.hset(self.uuid + "rules:org", org_id, "enable")
            self.redis.hset(self.uuid + "rules:org", key, value)

        script, expected = self.expect()
        luaScript = self.redis.register_script(script)
        for each in expected:
            result = each[-1]
            args = [str(x) for x in each[:-1]]
            redis_result = luaScript(
                keys=(
                    self.uuid + 'rules',
                    self.uuid + 'rules:trial',
                    self.uuid + 'rules:org'
                ),
                args=args
            )
            if redis_result:
                redis_result = redis_result.decode('ascii')
            self.assertEqual(
                result, redis_result,
                "The expected output for {} was {} but redis returned {}".format(
                    args, result, redis_result
                )
            )
