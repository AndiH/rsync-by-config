#!/usr/bin/env bats

load test_common

@test "List hosts" {
	run ../rbc.py --listhosts
	[ ${lines[2]} = "Specified entries in .sync.toml are:" ]
}

@test "Verbose output" {
	teardown() {
		cleanRemote
	}
	run ../rbc.py --verbose coba
	assert_output --partial 'Running rbc.py in verbose mode.'
}

@test "Dryrun" {
	run ../rbc.py --dryrun coba
	assert_output --partial '(DRY RUN)'
}

@test "Specify config file" {
	teardown() {
		cleanRemote
	}
	run ../rbc.py --config_file ".otherconfig.toml" otherhost
	assert_success
}
