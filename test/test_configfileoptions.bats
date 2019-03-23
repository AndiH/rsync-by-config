#!/usr/bin/env bats

load test_common

setup() {
	initRemote
}
teardown() {
	cleanRemote
}

@test "Default entry" {
	run ../rbc.py
	assert_output --partial "# Using default host lhost"
	assert_success
}

@test "Rsync options" {
	run ../rbc.py lhostVerbose
	assert_output --partial "opening connection using"
	assert_output --partial "(DRY RUN)"
	assert_success
}

@test "Source folder" {
	mkdir source
	echo "Testing Content" > source/test.txt
	run ../rbc.py lhostSource
	assert_output --partial "test.txt"
	assert_success
	rm -r source
}

@test "Global rsync options" {
	run ../rbc.py --config_file ".otherconfig.toml" otherhost
	assert_output --partial "opening connection using"
	assert_success
}

@test "Gathering" {
	../rbc.py lhost
	mkdir gather
	run ../rbc.py lhostInverse
	assert_file_exist gather/quote.txt
	assert_success
	rm -r gather
}

@test "Local transfers" {
	mkdir local
	run ../rbc.py local
	assert_file_exist local/quote.txt
	assert_success
	rm -r local
}

