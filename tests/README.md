# Tests for Rsync-by-Config

The tests in this directory are work in progress.

For testing, [Bats](https://github.com/sstephenson/bats) (the Bash Automated Testing System) is used, plus [*Bats test helpers*](https://github.com/ztombol/bats-support).

Currently implemented:

* `test.bats`: Some basic tests plus all those not fitting in other categories
* `test_cmdline.bats`: For command line parameters of RBC
* `test_exit.bats`: Test exit codes for common errors (which are not really caught exceptions but rather `exit(I)`s)

## Ressources for Travis

https://oncletom.io/2016/travis-ssh-deploy/
