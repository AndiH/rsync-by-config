#!/usr/bin/env bats

if [ "$(uname)" == "Darwin" ]; then
    SYSTEM="MAC"
elif [ "$(expr substr $(uname -s) 1 5)" == "Linux" ]; then
    SYSTEM="LINUX"
fi

if [[ $SYSTEM == "MAC" ]]; then
	PREFIX="$(brew --prefix)/lib"
elif [[ $SYSTEM == "LINUX" ]]; then
	PREFIX="$PWD/../test/test_helper"
fi
load "${PREFIX}/bats-support/load.bash"
load "${PREFIX}/bats-assert/load.bash"
load "${PREFIX}/bats-file/load.bash"

function initRemote() {
	ssh lhost "mkdir -p ~/tests/rbc/"
}

function cleanRemote() {
	ssh lhost "rm -rf ~/tests"
}

