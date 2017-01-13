#!/bin/sh
# https://github.com/ztombol/bats-support/blob/master/script/install-bats.sh
set -o errexit
set -o xtrace

git clone --depth 1 https://github.com/sstephenson/bats
cd bats && ./install.sh "${HOME}/.local" && cd .. && rm -rf bats
git clone https://github.com/ztombol/bats-support test/test_helper/bats-support
git clone https://github.com/ztombol/bats-assert.git test/test_helper/bats-assert
git clone https://github.com/ztombol/bats-file.git test/test_helper/bats-file
