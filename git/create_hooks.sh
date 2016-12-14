#!/bin/bash
cd "$(dirname "$0")"
cd ../.git/hooks
ln -s ../../git/hooks/* .
