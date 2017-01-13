#!/usr/bin/env bats

load test_common

@test "Config file exists" {
	run stat .sync.toml
	[ $status = 0 ]
}

@test "rbc.py exists in parent directory" {
	run stat ../rbc.py
	[ $status = 0 ]
}

@test "Sync with lhost host (current dir)" {
	teardown() {
		cleanRemote
	}
	run ../rbc.py lhost
	# [ ${lines[2]} = "sending incremental file list" ]
	assert_output --partial 'sending incremental file list'
}

@test "Sync with no host given (current dir)" {
	teardown() {
		cleanRemote
	}
	run ../rbc.py
	[ ${lines[2]} = "# Found default entry" ]
}

@test "Host unknown" {
	run ../rbc.py abc
	assert_output --partial "No entry abc is known in .sync.toml. Please edit the file!"
}
