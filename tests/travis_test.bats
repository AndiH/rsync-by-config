#!/usr/bin/env bats

load test_common

@test "Config file exists" {
	run stat .sync.toml
	[ $status = 0 ]
}
