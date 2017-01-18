#!/usr/bin/env bats

load test_common

setup() {
	initRemote
}
teardown() {
	cleanRemote
}

@test "Dry run" {
	export RBC_DRYRUN=1
	run ../rbc.py lhost
	assert_output --partial '(DRY RUN)'
}

@test "Specify config file" {
	export RBC_CONFIG_FILE=".otherconfig.toml"
	run ../rbc.py otherhost
	assert_success
}

@test "Give global rsync options" {
	export RBC_RSYNC_OPTIONS="--dry-run --verbose"
	run ../rbc.py lhost
	assert_output --partial "opening connection using"
	assert_output --partial "(DRY RUN)"
	assert_success
}
