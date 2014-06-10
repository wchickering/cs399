#!/bin/bash

# Joins every N lines of a file.

verify_number () {
    re='^[0-9]+$'
    if ! [[ $1 =~ $re ]] ; then
        die "error: Not a number: $1"
    fi
}

COMMAND=${0##*/}

while test $# -gt 0; do
    case "$1" in
        -h|--help)
            echo "$COMMAND - join every N lines"
            echo
            echo "Usage: $COMMAND [options] N file"
            echo
            echo "options:"
            echo "-h, --help                Show brief help"
            echo "--delim=STRING            Delimiter for joined lines"
            exit 0
            ;;
        --delim*)
            DELIM=`echo $1 | sed -e 's/^[^=]*=//g'`
            shift
            ;;
        *)
            break
            ;;
    esac
done

if [ $# -lt 2 ]; then
    die "Usage: $COMMAND [options] N file"
fi

# get args
N=$1
FILE=$2

verify_number $N

perl -pi -e "s/\r\n/$DELIM/ if $.%$N" $FILE 2> /dev/null
