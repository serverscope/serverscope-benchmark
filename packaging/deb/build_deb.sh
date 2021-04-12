#!/bin/bash

sudo apt-get install python3-all python-all dh-python python3-stem python3-stdeb -y

DIRA=$(dirname "$0")

pushd $DIRA/../../
rm -rf deb_dist/
rm -rf dist/
python3 setup.py --command-packages=stdeb.command sdist_dsc --depends3='curl, fio, make, gcc, perl' --upstream-version-suffix='.1'
cd $(ls -d to deb_dist/serverscope-benchmark-*/)
dpkg-buildpackage -rfakeroot -uc -us
popd
