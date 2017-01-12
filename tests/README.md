# Tests for Rsync-by-Config

The tests in this directory are work in progress.

For testing, [Bats](https://github.com/sstephenson/bats) (the Bash Automated Testing System) is used, plus [*Bats test helpers*](https://github.com/ztombol/bats-support).

Currently implemented:

* `test.bats`: Some basic tests plus all those not fitting in other categories
* `test_cmdline.bats`: For command line parameters of RBC
* `test_exit.bats`: Test exit codes for common errors (which are not really caught exceptions but rather `exit(I)`s)

## Ressources for Travis

* https://oncletom.io/2016/travis-ssh-deploy/
* https://gist.github.com/lukewpatterson/4242707
* https://gist.github.com/douglasduteil/5525750 (for `ssh_config`)

## Strategies to Test SSH Stuff

### Option A: Local SSH

Connect to local SSHD via 127.0.0.1

Problem: Apparently, sshd does not seem to run (and I can't get it to) inside Travis' docker image of their build environment

### Option B: Docker'ed SSH

Connect to a local SSH server, which is published by a docker image

* Docker image with SSHD: [`rastasheep/ubuntu-sshd`](https://hub.docker.com/r/rastasheep/ubuntu-sshd/)
```
docker pull rastasheep/ubuntu-sshd
docker run -d -P --name docker_sshd rastasheep/ubuntu-sshd
# docker port test_sshd 22
ssh …
```
* Pulling docker from [`.travis.yml`](https://docs.travis-ci.com/user/docker/):
```
services:
  - docker

before_install:
- docker pull carlad/sinatra
- docker run -d -p 127.0.0.1:80:4567 carlad/sinatra /bin/sh -c "cd /root/sinatra; bundle exec foreman start;"
- docker ps -a
- docker run carlad/sinatra /bin/sh -c "cd /root/sinatra; bundle exec rake test"
```
* Expose correct docker port:
* Generate SSH key
* Copy SSH key to shell (with [sshpass](https://neemzy.org/articles/deploy-to-your-own-server-through-ssh-with-travis-ci)?)
* Modify `~/.ssh/config` (https://gist.github.com/douglasduteil/5525750)

→ RESULT: There's a very very strange error that rsync is not found and or cannot connect to the host specified in the ssh_config

### Option C: Use Existing Remote Host

* Encrypt SSH private key with `travis encrypt`
* Put remote IP in environment variable (maybe encrypted [https://docs.travis-ci.com/user/encryption-keys/](https://docs.travis-ci.com/user/encryption-keys/)/[https://docs.travis-ci.com/user/environment-variables#Defining-Variables-in-.travis.yml](https://docs.travis-ci.com/user/environment-variables#Defining-Variables-in-.travis.yml))
