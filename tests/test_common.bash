#!/usr/bin/env bats

TEST_BREW_PREFIX="$(brew --prefix)"
load "${TEST_BREW_PREFIX}/lib/bats-support/load.bash"
load "${TEST_BREW_PREFIX}/lib/bats-assert/load.bash"

function cleanRemote() {
	ssh coba "rm ~/tests/rbc/*"
}
