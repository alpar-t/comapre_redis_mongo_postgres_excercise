#!/bin/bash
#
# Set up the virtual env, and bring up redis in docker bound to a random free local port,
# then run the unit tests passing in the specific port
#
set -e 

cd "$(dirname "$(realpath "$0")")";

REDIS_TEST_CONTAINER_NAME='rules-redis-test'
REDIS_TEST_DATA_VOLUME_NAME="${REDIS_TEST_CONTAINER_NAME=}-data"
REDIS_VERSION="3.0.7"

if ! [ -d venv ] ; then 
    echo "Creating virtual environment"
    virtualenv --python=python3 venv
fi

echo "Install dependencies..."
venv/bin/pip install -r requirements.txt --upgrade

echo "Starting redis in a container"
CONTAINER_STATUS=`docker inspect --format="{{ .State.Running }}"  $REDIS_TEST_CONTAINER_NAME 2>/dev/null || true`
if [ "$CONTAINER_STATUS" == "" ] ; then 
    echo "First time redis setup"
    docker volume create --name "${REDIS_TEST_CONTAINER_NAME}-data"
    docker create --name $REDIS_TEST_CONTAINER_NAME -P -v "$REDIS_TEST_DATA_VOLUME_NAME:/data" redis:$REDIS_VERSION
fi
if [ "$CONTAINER_STATUS" == "true" ] ; then 
    echo "Redis already running, restarting"
    docker stop $REDIS_TEST_CONTAINER_NAME > /dev/null
    docker wait $REDIS_TEST_CONTAINER_NAME > /dev/null
fi

docker run --rm --volumes-from $REDIS_TEST_CONTAINER_NAME redis:$REDIS_VERSION rm -rvf '/data/dump.rdb'
docker start $REDIS_TEST_CONTAINER_NAME > /dev/null

echo
export REDIS_PORT=`docker port $REDIS_TEST_CONTAINER_NAME 6379 | cut -d: -f2`
export PYTHONPATH=`realpath $PWD/../`:$PYTHONPATH
exec venv/bin/python -m unittest

