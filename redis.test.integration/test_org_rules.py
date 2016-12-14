# -*- mode: Python; tab-width: 4; indent-tabs-mode: nil; -*-
# ex: set tabstop=4 :
# Please do not change the lines above. See PEP 8, PEP 263.
""" Integration test for the lua rule engine

    Terminology:
    - specific prefix is generic in relation to annother one if it's inclued
      in it: 12 is generic when compared to 123
    - the inverse relation is called specific. 123 is more specific than 12
    - there is no relation between 123 and 23
"""
import redis_test

LUA_SCRIPT = "../phone.redis.lua"


class TrialSpecificTestCase(redis_test.LuaTestCase):
    """ Test decisions based on """

    def test_trial_only_restriction(self):
        """ Test that trial specific restrictions apply """
        self.given({
            "rules:trial": {
                "123": "restrict",
            }
        })
        self.expect((
            ("1234", "restrict"),
            ("1235", "restrict"),
            ("1335", None),
        ))

    def test_trial_fall_back_to_generic(self):
        """ If no trial rules are found, fall back to generic """
        self.given({
            "rules": {
                "123": "restrict",
            }
        })
        self.expect((
            ("1234", "restrict"),
            ("1235", "restrict"),
            ("1335", None),
        ))

    def test_trial_restrictions_generic(self):
        """ It should be possible for trial rules to restrict more generic
            prefixes even if there are generic rules to explicitly allow
            them """
        self.given({
            "rules": {
                "123": "restrict",
                "1235": "allow",
            },
            "rules:trial": {
                "123": "restrict",
            }
        })
        self.expect((
            ("1234", "restrict"),
            ("1235", "restrict"),
            ("1335", None),
        ))

    def test_trial_restrictions_specific(self):
        """ It shoudl be possible for trial rules to restrict more generic
            prefixes even if there are generic rules to explicitly allow
            them """
        self.given({
            "rules": {
                "123": "allow",
            },
            "rules:trial": {
                "1235": "restrict",
            }
        })
        self.expect((
            ("1234", "allow"),
            ("1235", "restrict"),
            ("1335", None),
        ))

    def test_trial_allowance(self):
        """ For now trial rules are allowed to relax permissions as well,
            we might want to restrict taht in the future, but for now,
            test that it works.
        """
        self.given({
            "rules": {
                "123": "restrict",
            },
            "rules:trial": {
                "1235": "allow",
            }
        })
        self.expect((
            ("1234", "restrict"),
            ("1235", "allow"),
            ("1335", None),
        ))
        # would be nice toe have tooling to be able to access the redis
        # log here and check that a warning was issued

    def expect(self, expected_result):
        return super(TrialSpecificTestCase, self).expect(
            self.load_script(LUA_SCRIPT),
            [(x[0], True, "any-org-id", x[1]) for x in expected_result]
        )


class TrialCrosstalkTestCase(TrialSpecificTestCase):
    """ Test that the presence of org specific rules does not affect
    decisions for non org specific queries """

    def test_trial_only_restriction(self):
        self.given({
            "rules:org": {
                "123": "allow",
            }
        })
        super(TrialCrosstalkTestCase, self).test_trial_only_restriction()

    def test_trial_fall_back_to_generic(self):
        self.given({
            "rules:org": {
                "123": "allow",
            }
        })
        super(TrialCrosstalkTestCase, self).test_trial_fall_back_to_generic()

    def test_trial_restrictions_generic(self):
        self.given({
            "rules:org": {
                "123": "allow",
                "1235": "allow",
            }
        })
        super(TrialCrosstalkTestCase, self).test_trial_restrictions_generic()

    def test_trial_restrictions_specific(self):
        self.given({
            "rules:org": {
                "1235": "allow",
            }
        })
        super(TrialCrosstalkTestCase, self).test_trial_restrictions_specific()

    def test_trial_allowance(self):
        self.given({
            "rules:org": {
                "1235": "restrict",
            }
        })
        super(TrialCrosstalkTestCase, self).test_trial_allowance()
