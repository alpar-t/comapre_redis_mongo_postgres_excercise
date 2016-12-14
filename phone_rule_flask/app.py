# -*- mode: Python; tab-width: 4; indent-tabs-mode: nil; -*-
# ex: set tabstop=4 :
# Please do not change the lines above. See PEP 8, PEP 263.

import os
from flask import Flask
from flask import request
from flask_redis import FlaskRedis
from phone_rule_engine import RuleOperations


app = Flask(__name__)
app.config["REDIS_URL"] = os.environ.get(
    "REDIS_URL", "redis://localhost:6379/0"
)
rules_op = RuleOperations(FlaskRedis(app))


@app.before_request
def check_if_can_call():
    phone_number = request.view_args.get("phone_number")
    if not phone_number:
        return
    is_trial = request.args.get('is_trial')
    org_id = request.args.get('org_id')
    rule = rules_op.query_rule(phone_number, is_trial, org_id)
    if rule:
        app.logger.info(
            "Allowing call to (%s, %s, %s) based on explicit rule",
            phone_number, is_trial, org_id
        )
        return
    if rule is None:
        app.logger.info(
            "Implicitly allowing call to (%s, %s, %s)",
            phone_number, is_trial, org_id
        )
        return
    app.logger.info(
        "Blocking call to (%s, %s, %s)",
        phone_number, is_trial, org_id
    )
    return "Calls to this number are not allowed\n", 200


@app.route("/phone_call/<phone_number>", methods=("POST", ))
def hello(phone_number):
    is_trial = request.args.get('is_trial')
    org_id = request.args.get('org_id')
    return "Calling {} (is_trial: {}, org_id: {}) ...\n".format(
        phone_number, is_trial, org_id
    )


if __name__ == "__main__":
    app.run()
