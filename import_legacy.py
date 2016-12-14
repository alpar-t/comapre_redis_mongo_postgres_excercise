# -*- mode: Python; tab-width: 4; indent-tabs-mode: nil; -*-
# ex: set tabstop=4 :
# Please do not change the lines above. See PEP 8, PEP 263.
"""
 Load the legacy data in redis

 Possible optimizations:
  - load all generic prefixes in trial rules as well
     - this will lead to fewer lookups for trial custommers
  - load specific allowing rules for any prefix that is not restricted
     - this would make it possible to invlaidate a None result form redis
     - would help if for some reason the script or the data in redis are
       corrupted / missing and no rule is found, we could still
       preventively block calls ( even trough we might be over blocking )
       to prevent excessive costs
"""
import redis
import argparse
from phone_rule_engine import RuleOperations
import phone_legacy_data


def parse_args():
    parser = argparse.ArgumentParser(
        description='Import the hardcoded data into redis'
    )
    parser.add_argument("--host", default="localhost",
                        help="redis host to connect to")
    parser.add_argument("--port", default="6379",
                        help="redis port to connect to")
    return parser.parse_args()


def main():
    args = parse_args()
    rule_ops = RuleOperations(
        redis.StrictRedis(host=args.host, port=args.port)
    )
    for prefix in phone_legacy_data.RESTRICTED_OUTBOUND_PAYING_PREFIXES.keys():
        rule_ops.push_generic_rule(prefix, rule_ops.R_RESTRICT)
    print("Imported {} general rules".format(
        len(phone_legacy_data.RESTRICTED_OUTBOUND_PAYING_PREFIXES.keys())
    ))
    for prefix in phone_legacy_data.RESTRICTED_OUTBOUND_TRIAL_PREFIXES.keys():
        rule_ops.push_generic_rule(prefix, rule_ops.R_RESTRICT)
    print("Imported {} trial rules".format(
        len(phone_legacy_data.RESTRICTED_OUTBOUND_TRIAL_PREFIXES.keys())
    ))

if __name__ == "__main__":
    main()
