#!/usr/bin/env bats

load test_common

setup() {
	initRemote
}
teardown() {
	cleanRemote
}

@test "Help message" {
	run ../rbc.py --help
	assert_output --partial "Usage: rbc.py [OPTIONS] [ENTRY]"
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

@test "Additional rsync option" {
	run ../rbc.py lhost --rsync_options "--dry-run"
	assert_output --partial "(DRY RUN)"
	assert_success
}

@test "Multiple additional rsync options" {
	run ../rbc.py lhost --rsync_options "--dry-run" --rsync_options "--partial" "--verbose"
	assert_output --partial "All rsync options:"
	assert_output --partial "(DRY RUN)"
	assert_success
}
