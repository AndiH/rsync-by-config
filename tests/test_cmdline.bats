#!/usr/bin/env bats

load test_common

@test "List hosts" {
	run ../rbc.py --listhosts
	assert_output --partial "Specified entries in .sync.toml are:"
}

@test "Verbose output" {
	setup() {
		initRemote
	}
	teardown() {
		cleanRemote
	}
	run ../rbc.py --verbose lhost
	assert_output --partial 'Running rbc.py in verbose mode.'
}

@test "Dryrun" {
	setup() {
		initRemote
	}
	teardown() {
		cleanRemote
	}
	run ../rbc.py --dryrun lhost
	assert_output --partial '(DRY RUN)'
}

@test "Specify config file" {
	teardown() {
		cleanRemote
	}
	run ../rbc.py --config_file ".otherconfig.toml" otherhost
	assert_success
}
