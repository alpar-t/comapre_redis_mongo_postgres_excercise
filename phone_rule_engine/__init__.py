# -*- mode: Python; tab-width: 4; indent-tabs-mode: nil; -*-
# ex: set tabstop=4 :
# Please do not change the lines above. See PEP 8, PEP 263.
""" Operations to deal with phone prefix rules """

from functools import lru_cache
import os

LUA_SCRIPT_NAME = "phone.redis.lua"

class RuleOperations(object):
    """ Operations to deal with phone prefix rules """

    def __init__(self, redis, key_prefix=""):
        self.redis = redis
        self.key_prefix = key_prefix
        if self.key_prefix:
            self.key_prefix += ":"

    def push_generic_rule(self, prefix, rule):
        """ Sets a generic rule for the specific prefix """
        self._push_rule("rules", prefix, rule)

    def push_trial_rule(self, prefix, rule):
        """ Sets a trial specific rule for the specific prefix """
        self._push_rule("rules:trial", prefix, rule)

    def push_org_rule(self, prefix, rule, org_id):
        """ Push an organization sepcific rule  """
        prefix = self._prefix(prefix)
        rule = self._rule(rule)
        self.redis.hset(self.key_prefix + "rules:org", org_id, "enable")
        self.redis.hset(
            self.key_prefix + "rules:org",
            "{}:{}".format(org_id, prefix),
            rule
        )

    @lru_cache()
    def _load_script(self):
        """ Loads the path specified in argumenta and memoizes """
        path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            LUA_SCRIPT_NAME
        )
        with open(path, 'r') as script:
            return script.read()

    def query_rule(self, phone_no, is_trial=False, org_id=None):
        """ Query redis for the policy to apply

            Trial status and organisation is also accounted for.
            Returns True if the  phone_no is allowed, False if it's restricted
            or None if there's no rule

            Raises ValueError if invalid rule is found in redis
        """
        lua_script = self.redis.register_script(
            self._load_script()
        )
        ret = lua_script(
            keys=(
                self.key_prefix + 'rules',
                self.key_prefix + 'rules:trial',
                self.key_prefix + 'rules:org'
            ),
            args=(
                phone_no, is_trial, org_id
            )
        )
        if ret:
            ret = ret.decode('ascii')
            if ret == "allow":
                return True
            if ret == "restrict":
                return False
            raise ValueError("Invalid rule in redis: {}".format(ret))
        else:
            return None

    @staticmethod
    def _rule(rule):
        """ Validate and normalize the rule """
        rule = rule.lower()
        if rule not in ("allow", "restrict"):
            raise ValueError("Rule has to be one of: allow or restrict, " +
                             "but it was: {}".format(rule))
        return rule

    @staticmethod
    def _prefix(prefix):
        """ validate and normalize the prefix """
        if prefix.startswith("+"):
            prefix = prefix[1:]
        if not prefix.isdigit():
            raise ValueError(
                "Phone prefix can only contain numbers: {}".format(prefix)
            )
        return prefix

    def _push_rule(self, key, prefix, rule):
        """ Adds the rule for prefix to the specific key in redis

            Returns any rule that was set previusly
        """
        prefix = self._prefix(prefix)
        rule = self._rule(rule)
        self.redis.hset(self.key_prefix + key, prefix, rule.lower())
