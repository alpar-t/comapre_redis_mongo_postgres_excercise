#!/bin/bash

set -e 

cd "$(dirname "$(realpath "$0")")";

if ! [ -d venv ] ; then 
    echo "Creating virtual environment"
    virtualenv --python=python3 venv
fi

echo "Install dependencies..."
venv/bin/pip install -r requirements.txt --upgrade

export PYTHONPATH=`realpath $PWD/../`:$PYTHONPATH
export REDIS_URL="redis://localhost:`docker port rules-redis-test 6379 | cut -d: -f2`/0"
exec venv/bin/python3 app.py
