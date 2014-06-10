#!/bin/bash

# Joins every N lines of a file.

verify_number () {
    re='^[0-9]+$'
    if ! [[ $1 =~ $re ]] ; then
        die "error: Not a number: $1"
    fi
}

# get args
N=$1
FILE=$2

verify_number $N

perl -pi -e "s/\r\n/ / if $.%$N" $FILE 2> /dev/null
