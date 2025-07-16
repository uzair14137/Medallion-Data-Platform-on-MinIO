#!/usr/bin/env bash
#   Use this script to test if a given TCP host/port are available
#
#   Licensed under the MIT license:
#   https://opensource.org/licenses/MIT

set -e

TIMEOUT=15
QUIET=0
HOST=""
PORT=""

echoerr() { if [ "$QUIET" -ne 1 ]; then echo "$@" 1>&2; fi }

usage()
{
    cat << USAGE >&2
Usage:
    $0 host:port [-s] [-t timeout] [-- command args]
    -h HOST | --host=HOST       Host or IP to check
    -p PORT | --port=PORT       TCP port to check
    -s | --strict               Only execute subcommand if the test succeeds
    -q | --quiet                Don't output any status messages
    -t TIMEOUT | --timeout=TIMEOUT
                                Timeout in seconds, zero for no timeout
    -- COMMAND ARGS             Execute command with args after the test finishes
USAGE
    exit 1
}

wait_for()
{
    if [[ "$TIMEOUT" -gt 0 ]]; then
        echoerr "Waiting $TIMEOUT seconds for $HOST:$PORT"
    else
        echoerr "Waiting for $HOST:$PORT without a timeout"
    fi
    start_ts=$(date +%s)
    while :
    do
        if nc -z "$HOST" "$PORT"; then
            end_ts=$(date +%s)
            echoerr "$HOST:$PORT is available after $((end_ts-start_ts)) seconds"
            break
        fi
        sleep 1
        if [[ "$TIMEOUT" -gt 0 ]]; then
            now_ts=$(date +%s)
            if [[ $((now_ts-start_ts)) -ge $TIMEOUT ]]; then
                echoerr "Timeout occurred after waiting $TIMEOUT seconds for $HOST:$PORT"
                exit 1
            fi
        fi
    done
    return 0
}

while [[ $# -gt 0 ]]
do
    case "$1" in
        *:* )
        HOSTPORT=(${1//:/ })
        HOST=${HOSTPORT[0]}
        PORT=${HOSTPORT[1]}
        shift 1
        ;;
        -q | --quiet)
        QUIET=1
        shift 1
        ;;
        -s | --strict)
        STRICT=1
        shift 1
        ;;
        -h)
        HOST="$2"
        if [ "$HOST" == "" ]; then break; fi
        shift 2
        ;;
        --host=*)
        HOST="${1#*=}"
        shift 1
        ;;
        -p)
        PORT="$2"
        if [ "$PORT" == "" ]; then break; fi
        shift 2
        ;;
        --port=*)
        PORT="${1#*=}"
        shift 1
        ;;
        -t)
        TIMEOUT="$2"
        if [ "$TIMEOUT" == "" ]; then break; fi
        shift 2
        ;;
        --timeout=*)
        TIMEOUT="${1#*=}"
        shift 1
        ;;
        --)
        shift
        CMD=("$@")
        break
        ;;
        --help)
        usage
        ;;
        *)
        echoerr "Unknown argument: $1"
        usage
        ;;
    esac
done

if [[ "$HOST" == "" || "$PORT" == "" ]]; then
    echoerr "Error: you need to provide a host and port to test."
    usage
fi

wait_for

if [[ "$CMD" != "" ]]; then
    exec "${CMD[@]}"
fi

exit 0
