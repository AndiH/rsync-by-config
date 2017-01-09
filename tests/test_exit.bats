#!/usr/bin/env bats

load test_common

@test "Wrong config filename" {
	run ../rbc.py --config_file notthere.toml
	assert_failure 3
}

@test "Entry unknown" {
	run ../rbc.py failentry
	assert_failure 4
}

@test "Wrong source folder" {
	run ../rbc.py wrongsource
	assert_failure 6
}

@test "No target folder" {
	run ../rbc.py notarget
	assert_failure 7
}

@test "Local transfer (no hostname), but wrong target folder" {
	run ../rbc.py localbutwrongsource
	assert_failure 8
}
