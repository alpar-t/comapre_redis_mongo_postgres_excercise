#!/bin/bash

set -e 

cd "$(dirname "$(realpath "$0")")";

echo "Checking environment"
./env_check.sh 

echo "Ruinning unit tests"
./phone_rule_engine/test.sh

echo "Runing Redis integration tests"
./redis_test_integration/test.sh

echo "Importing rules to redis"
phone_rule_engine/venv/bin/python3 import_legacy.py --port=`docker port rules-redis-test 6379 | cut -d: -f2`

URL_BASE='http://127.0.0.1:5000/phone_call'

echo "Starting flask app..."
./phone_rule_flask/run.sh &
while ! curl $URL_BASE 2> /dev/null > /dev/null ; do
    :
done

function finish {
    echo -e "\e[0mStopping flask app..."
    kill %1
}
trap finish EXIT

STATUS=0
check() {
    local ret=`curl -s -X POST $1`
    if ! echo $ret | grep -q "$2" ; then
        echo -e "\e[31mExpected '$2' but got: $ret\e[37m"
        STATUS=1
    else
        echo -e  "\e[92m$ret \e[37m"
    fi
}

echo
echo "+--------------------------+"
echo "| Running end to end tests |"
echo "+--------------------------+"
echo -e "\e[37m"

check "$URL_BASE/40744931029?is_trial=True&org_id=foo" "^Calling"
check "$URL_BASE/211744931029?is_trial=True&org_id=foo" "not allowed$"
check "$URL_BASE/1242744931029?is_trial=False&org_id=foo" "^Calling"
check "$URL_BASE/1242744931029?is_trial=True&org_id=foo" "not allowed$"

exit $STATUS

