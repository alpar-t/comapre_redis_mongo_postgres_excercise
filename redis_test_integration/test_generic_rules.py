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

LUA_SCRIPT = "../phone_rule_engine/phone.redis.lua"


class GenericTestCase(redis_test.LuaTestCase):
    """ Test decisions based on generic rules  """

    def test_no_decision_with_no_rules(self):
        """ No rules, no decision """
        self.expect((
            ("1", None),
            ("12", None),
            ("40744931029", None),
        ))

    def test_simple_decisions(self):
        """ If there's a rule, echo the decision """
        self.given({
            "rules": {
                "23": "restrict",
                "45": "allow",
            }
        })
        self.expect((
            ("23", "restrict"),
            ("23456", "restrict"),
            ("45", "allow"),
            ("4567", "allow"),
            ("1", None),
            ("12", None),
            ("40744931029", None),
        ))

    def test_nested_decisions(self):
        """ Allow a more specific subset when a less specific is restricted """
        self.given({
            "rules": {
                "123": "restrict",
                "1235": "allow",
                "67": "allow",
                "678": "restrict",
            }
        })

        self.expect((
            ("1234", "restrict"),
            ("12356", "allow"),
            ("670", "allow"),
            ("6780", "restrict"),
            ("1", None),
            ("12", None),
            ("40744931029", None),
        ))

    def test_multi_level_nesting(self):
        """ Test varius levels of nesting rules """
        self.given({
            "rules": {
                "1": "restrict",
                "12": "allow",
                "123": "restrict",
                "1234": "allow",
            }
        })

        self.expect((
            ("1234", "allow"),
            ("12340", "allow"),
            ("123", "restrict"),
            ("1230", "restrict"),
            ("12", "allow"),
            ("120", "allow"),
            ("1", "restrict"),
            ("10", "restrict"),
        ))

    def expect(self, expected_result):
        return super(GenericTestCase, self).expect(
            self.load_script(LUA_SCRIPT),
            [(x[0], False, "any-org-id", x[1]) for x in expected_result]
        )


class NoCrosstalkTestCase(GenericTestCase):
    """ Test that the presence of trial and org rules does not affect
    decisions for non trial non organization specific queries """

    def test_no_decision_with_no_rules(self):
        self.given({
            "rules:trial": {
                "1": "restrict",
                "12": "allow",
                "40": "allow",
            },
            "rules:org": {
                "1": "restrict",
                "12": "allow",
                "40": "allow",
            }
        })
        super(NoCrosstalkTestCase, self).test_no_decision_with_no_rules()

    def test_simple_decisions(self):
        self.given({
            "rules:trial": {
                "23": "allow",
                "45": "restrict",
            },
            "rules:org": {
                "23": "allow",
                "45": "restrict",
            }
        })
        super(NoCrosstalkTestCase, self).test_simple_decisions()

    def test_nested_decisions(self):
        self.given({
            "rules:trial": {
                "123": "allow",
                "1235": "restrict",
                "67": "restrict",
                "678": "allow",
            },
            "rules:org": {
                "123": "allow",
                "1235": "restrict",
                "67": "restrict",
                "678": "allow",
            },
        })
        super(NoCrosstalkTestCase, self).test_nested_decisions()

    def test_multi_level_nesting(self):
        self.given({
            "rules:trial": {
                "1": "allow",
                "12": "restrict",
                "123": "allow",
                "1234": "restrict",
            },
            "rules:org": {
                "1": "allow",
                "12": "restrict",
                "123": "allow",
                "1234": "restrict",
            },
        })
        super(NoCrosstalkTestCase, self).test_multi_level_nesting()
