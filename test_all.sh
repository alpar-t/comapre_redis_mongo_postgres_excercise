#!/bin/bash 

set -e 

cd "$(dirname "$(realpath "$0")")";

echo "Checking environment"
./env_check.sh 

echo
echo "Runing Redis integration tests"
./redis_test_integration/run.sh
