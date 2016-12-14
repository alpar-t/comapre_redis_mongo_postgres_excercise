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


class OrganisationSpecificTestCase(redis_test.LuaTestCase):
    """ Test organisation sepcific rules """

    def test_org_specific_allowance(self):
        """ Org specific rules should be stronger than generic rules """
        self.given({
            "rules": {
                "123": "restrict",
            },
            "rules:org": {
                "123": "allow"
            }
        })
        self.expect_non_trial((
            ("123", "allow"),
            ("1230", "allow"),
        ))

    def test_org_specific_allowance_trial(self):
        """ Org specific rules should be stronger than generic
            and trial rules """
        self.given({
            "rules": {
                "12": "restrict",
            },
            "rules:trial": {
                "123": "restrict",
            },
            "rules:org": {
                "1234": "allow"
            }
        })
        self.expect_for_trial((
            ("120", "restrict"),
            ("1230", "restrict"),
            ("12340", "allow"),
        ))

    def test_org_specific_restriction(self):
        """ Org specific rules can be restrictive for now  """
        self.given({
            "rules": {
                "12": "allow",
            },
            "rules:trial": {
                "123": "allow",
            },
            "rules:org": {
                "1234": "restrict"
            }
        })
        self.expect_for_trial((
            ("123", "allow"),
            ("1230", "allow"),
            ("1234", "restrict"),
            ("12340", "restrict"),
        ))

    def test_org_nesting(self):
        """ Test that nesting works at the org level as well """
        self.given({
            "rules": {
                "1": "restrict",
            },
            "rules:org": {
                "12": "allow",
                "123": "restrict"
            }
        })
        self.expect_non_trial((
            ("10", "restrict"),
            ("120", "allow"),
            ("1230", "restrict"),
        ))

    def test_org_nesting_trial(self):
        """ Test that nesting works at the org and trial levels as well """
        self.given({
            "rules": {
                "1": "restrict",
            },
            "rules:trial": {
                "12": "allow",
            },
            "rules:org": {
                "123": "restrict"
            }
        })
        self.expect_for_trial((
            ("10", "restrict"),
            ("120", "allow"),
            ("1230", "restrict"),
        ))

    def expect_non_trial(self, expected_result):
        """ equivalent to expect(False, ...) for better readability """
        return self.expect(False, expected_result)

    def expect_for_trial(self, expected_result):
        """ equivalent to expect(True, ...) for better readability """
        return self.expect(True, expected_result)

    def expect(self, isTrial, expected_result):
        return super(OrganisationSpecificTestCase, self).expect(
            self.load_script(LUA_SCRIPT),
            [(x[0], isTrial, self.test_org_id, x[1]) for x in expected_result]
        )
