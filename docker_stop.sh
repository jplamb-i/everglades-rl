#!/usr/bin/env bash
function kill(){
    docker kill $(docker ps -q)
    return 0
    }
kill
