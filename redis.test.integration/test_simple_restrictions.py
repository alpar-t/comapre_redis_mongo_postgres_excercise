# -*- mode: Python; tab-width: 4; indent-tabs-mode: nil; -*-
# ex: set tabstop=4 :
# Please do not change the lines above. See PEP 8, PEP 263.

import redis_test

class TestRulesEngine(redis_test.LuaTestCase):

    @staticmethod
    def given():
        return {
            "rules": {
                "123": "restrict",
                "1235": "allow",
            }
        }

    def expect(self):
        return self.load_script("../phone.redis.lua"), (
            ("1234", True, "restrict"),
            ("12356", True, "allow"),
            ("1", True,  None),
            ("12", True,  None),
            ("40744931029", True,  None),
        )
