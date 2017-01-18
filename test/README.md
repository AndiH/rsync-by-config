# Tests for Rsync by Config

[![Build Status](https://travis-ci.org/AndiH/rsync-by-config.svg?branch=master)](https://travis-ci.org/AndiH/rsync-by-config)

For testing Rsync-By-Config, [Bats](https://github.com/sstephenson/bats) (the Bash Automated Testing System) is used, plus [*Bats test helpers*](https://github.com/ztombol/bats-support). Building and testing is done with Travis CI.

## Status of Implementation

Currently implemented:

* `test.bats`: Some basic tests plus all those not fitting in other categories
* `test_cmdline.bats`: For command line parameters of RBC
* `test_envvars.bats`: Click exposes all command line options also as environment variables; this is the according test
* `test_exitcode.bats`: Test exit codes for common errors (which are not really caught exceptions but rather `exit(I)`s)
* `test_configfileoptions.bats`: Test all options of the config file.

Not yet implemented:

* `test_monitor.bats`: This should test the monitoring feature of RBC. Unfortunately I can't get the needed background process to work

## Travis Setup

On Travis, a docker container with an SSH daemon is pulled and started, forwarding port 2222 into the container. `rsync` is installed to it and the host's public key copied. The SSH docker container is used for all the testing, usually called `lhost`.
