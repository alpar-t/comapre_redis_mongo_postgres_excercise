#!/bin/bash

assure() {
    found=`which $1`
    if [ -z "$found" ] ; then
        echo "Could not find '$1', make sure it's installed and available on the path"
        exit 1
    fi
    echo "$1 -> $found"
}

assure docker 
assure python3
assure virtualenv

