#!/usr/bin/env bats

load test_common

@test "Monitoring one host" {
	skip # apparently, bats can't handle self-spawned background processes properly :(
	../rbc.py --monitor > out.log > err.log & export APP_ID=$!
	touch tmp
	touch tmp
	kill -SIGINT $APP_ID
	run cat out.log | grep "Synced 2 times"
	assert_success
}
