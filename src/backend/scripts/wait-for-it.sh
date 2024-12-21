#!/usr/bin/env bash
# Version: 1.0.0
# wait-for-it.sh - Test and wait for the availability of a TCP host and port

# Strict error handling
set -e
set -o pipefail
set -u

# Global variables
TIMEOUT=15
QUIET=0
PROTOCOL="tcp"
VERBOSE=0
CHILD_PID=""
RETRY_INTERVAL=1

# Cleanup handler
cleanup() {
    local pids
    if [ -n "$CHILD_PID" ]; then
        kill -TERM "$CHILD_PID" 2>/dev/null || true
        wait "$CHILD_PID" 2>/dev/null || true
    fi
    # Kill any remaining background processes
    pids=$(jobs -p)
    if [ -n "$pids" ]; then
        kill -TERM $pids 2>/dev/null || true
        wait $pids 2>/dev/null || true
    fi
}

# Set up signal traps
trap cleanup SIGTERM SIGINT SIGQUIT EXIT

# Usage information
usage() {
    cat << USAGE >&2
Usage: $0 [-q] [-v] [-t timeout] host:port [-- command args]
   -q | --quiet                        Don't output any status messages
   -v | --verbose                      Verbose mode with detailed output
   -t TIMEOUT | --timeout=TIMEOUT      Timeout in seconds, zero for no timeout
   -- COMMAND ARGS                     Execute command with args after the test
   -h | --help                         Show this help message

Examples:
    $0 localhost:5432                  # Wait for PostgreSQL
    $0 -t 30 redis:6379               # Wait up to 30 seconds for Redis
    $0 rabbitmq:5672 -- echo "Ready"  # Wait for RabbitMQ and run command

Exit Codes:
    0 - Success
    1 - Timeout
    2 - Invalid arguments
    3 - Connection error
USAGE
    exit 2
}

# Log message if not in quiet mode
echoerr() {
    if [ "$QUIET" -ne 1 ]; then
        printf "%s\n" "$*" 1>&2
    fi
}

# Verbose logging
log_verbose() {
    if [ "$VERBOSE" -eq 1 ]; then
        echoerr "$@"
    fi
}

# Wait for a TCP connection
wait_for() {
    local host="$1"
    local port="$2"
    local timeout="$3"
    local start_ts
    local end_ts
    local result

    if [[ "$host" == "" || "$port" == "" ]]; then
        echoerr "Error: Host and port are required"
        return 2
    fi

    if ! [[ "$port" =~ ^[0-9]+$ ]] || [ "$port" -lt 1 ] || [ "$port" -gt 65535 ]; then
        echoerr "Error: Invalid port number: $port"
        return 2
    fi

    start_ts=$(date +%s)
    if [ "$timeout" -gt 0 ]; then
        end_ts=$((start_ts + timeout))
    fi

    while true; do
        (echo > "/dev/tcp/$host/$port") >/dev/null 2>&1
        result=$?
        
        if [ $result -eq 0 ]; then
            log_verbose "Connected to $host:$port"
            return 0
        fi

        if [ "$timeout" -gt 0 ] && [ "$(date +%s)" -ge "$end_ts" ]; then
            echoerr "Timeout occurred after waiting $timeout seconds for $host:$port"
            return 1
        fi

        log_verbose "Waiting for $host:$port... ($(date))"
        sleep "$RETRY_INTERVAL"
    done
}

# Parse command line arguments
parse_arguments() {
    local args=("$@")
    local host=""
    local port=""
    local timeout="$TIMEOUT"
    local command=()
    local i=0

    while [ $i -lt ${#args[@]} ]; do
        case "${args[$i]}" in
            -q | --quiet)
                QUIET=1
                ;;
            -v | --verbose)
                VERBOSE=1
                ;;
            -t)
                i=$((i + 1))
                timeout="${args[$i]}"
                if ! [[ "$timeout" =~ ^[0-9]+$ ]]; then
                    echoerr "Error: Invalid timeout value"
                    usage
                fi
                ;;
            --timeout=*)
                timeout="${args[$i]#*=}"
                if ! [[ "$timeout" =~ ^[0-9]+$ ]]; then
                    echoerr "Error: Invalid timeout value"
                    usage
                fi
                ;;
            -h | --help)
                usage
                ;;
            --)
                i=$((i + 1))
                command=("${args[@]:$i}")
                break
                ;;
            *)
                if [[ "${args[$i]}" == *":"* ]]; then
                    host="${args[$i]%:*}"
                    port="${args[$i]#*:}"
                else
                    echoerr "Error: Invalid host:port format"
                    usage
                fi
                ;;
        esac
        i=$((i + 1))
    done

    if [[ -z "$host" || -z "$port" ]]; then
        echoerr "Error: Host and port are required"
        usage
    fi

    echo "$host" "$port" "$timeout" "${command[@]+"${command[@]}"}"
}

# Main execution
main() {
    local parsed
    local host
    local port
    local timeout
    local command=()

    # Parse arguments
    read -r host port timeout command < <(parse_arguments "$@")

    # Wait for service
    log_verbose "Waiting for $host:$port with timeout $timeout seconds"
    wait_for "$host" "$port" "$timeout"
    result=$?

    # Execute command if provided
    if [ ${#command[@]} -gt 0 ]; then
        if [ $result -ne 0 ]; then
            echoerr "Service $host:$port did not start within timeout"
            exit $result
        fi
        
        log_verbose "Executing command: ${command[*]}"
        exec "${command[@]}"
    fi

    return $result
}

# Execute main if not sourced
if ! (return 0 2>/dev/null); then
    main "$@"
fi