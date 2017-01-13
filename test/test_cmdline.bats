#!/usr/bin/env bats

load test_common

setup() {
	initRemote
}
teardown() {
	cleanRemote
}

@test "List hosts" {
	run ../rbc.py --listhosts
	assert_output --partial "Specified entries in .sync.toml are:"
}

@test "Verbose output" {
	run ../rbc.py --verbose lhost
	assert_output --partial 'Running rbc.py in verbose mode.'
}

@test "Dryrun" {
	run ../rbc.py --dryrun lhost
	assert_output --partial '(DRY RUN)'
}

@test "Specify config file" {
	run ../rbc.py --config_file ".otherconfig.toml" otherhost
	assert_success
}
