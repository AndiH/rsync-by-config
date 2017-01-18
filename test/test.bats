#!/usr/bin/env bats

load test_common

@test "Config file exists" {
	# run stat .sync.toml
	# [ $status = 0 ]
	assert_file_exist .sync.toml
}

@test "rbc.py exists in parent directory" {
	# run stat ../rbc.py
	# [ $status = 0 ]
	assert_file_exist ../rbc.py
}

@test "Sync with lhost host (current dir)" {
	setup() {
		initRemote
	}
	teardown() {
		cleanRemote
	}
	run ../rbc.py lhost
	# [ ${lines[2]} = "sending incremental file list" ]
	assert_output --partial 'sending incremental file list'
}

@test "Host unknown" {
	run ../rbc.py abc
	assert_output --partial "No entry abc is known in .sync.toml. Please edit the file!"
}
