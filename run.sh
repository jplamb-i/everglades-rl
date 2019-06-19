#!/usr/bin/env bash

t_flag=1  # training mode
r_flag=1  # render mode
print_usage() {
    printf "Usage: %s:\n [-r] Render telemetry\n [-t] Training mode\n" $0
}

while getopts 'tr' flag; do
    case "${flag}" in
        r) r_flag=0 ;;
        t) t_flag=0 ;;
        *) print_usage
            exit 1 ;;
    esac
done

if [ "$(uname)" == "Darwin" ]; then
    # is Mac
    has_cuda=$([ -f /usr/local/cuda/version.txt ])
elif [ "$(expr substr $(uname -s) 1 5)" == "Linux" ]; then
    # is Linux
    has_cuda=$([ -f /usr/local/cuda/version.txt ])
elif [ "$(expr substr $(uname -s) 1 10)" == "MINGW32_NT" ]; then
    # Do something under 32 bits Windows NT platform
    pass
elif [ "$(expr substr $(uname -s) 1 10)" == "MINGW64_NT" ]; then
    # Do something under 64 bits Windows NT platform
    pass
fi

if [ "$t_flag" == 0 ]; then
    echo "Training mode"
    export everglades_agent_is_training=1
else
    export everglades_agent_is_training=0
fi

if [ "$has_cuda" == 0 ]; then
    echo "Using nvidia container"
    export agent_image=everglades-agent-gpu
    export runtime=nvidia
else
    echo "CUDA not detected, not using nvidia docker"
    export agent_image=everglades-agent
    export runtime=docker
fi

docker-compose up

if [ "$r_flag" == 0 ]; then
    echo "I should be rendering something now"
fi