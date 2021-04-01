#!/bin/bash

if [ `whoami` != 'root' ]; then
  echo "You must be root to run tests"
  exit 1
fi

cat /etc/os-release | grep -E 'Ubuntu|Debian' > /dev/null
  if [ $? -ne 0 ]; then
    echo "Test is intended to be run on Ubuntu/Debian, exiting"
  exit 1
fi

source /etc/os-release

dpkg-query -l | grep debootstrap > /dev/null
if [ $? -ne 0 ]; then
    echo "debootstrap package is required for testing"
    echo "use: apt-get install debootstrap"
    exit 1
fi


if [ "$(pwd)" == "/" ]; then
    echo "It's prohibided to be run from system root (/)!"
    exit 1
fi

RELVER=$UBUNTU_CODENAME
if [ -z $RELVER ]; then
  RELVER=$VERSION_CODENAME
  if [ -z $RELVER ]; then
    echo "This is not a valid Ubuntu/Debian release, aborting..."
    exit 1
  fi
  echo "Bootstrapping for Debian $RELVER"
  RELURL="http://deb.debian.org/debian/"
else
  echo "Bootstrapping for Ubuntu $RELVER"
  RELURL="http://archive.ubuntu.com/ubuntu/"
fi
TESTROOT=$(pwd)/testroot-$RELVER/
SS_DIR=$TESTROOT/tmp/ss_dir
RESULT="1"
DEPS_LIST="make perl fio gcc python3-setuptools python3-distro python3-requests curl locales"
DIRA=$(dirname "$0")

function __setup_testroot() {
    mount --bind /proc $TESTROOT/proc
    mount --bind -o ro /etc/apt/sources.list $TESTROOT/etc/apt/sources.list
    mount --bind -o ro  /etc/resolv.conf $TESTROOT/etc/resolv.conf
}

function __clean_up_testroot() {
  # clean up

  if [[ "$TESTROOT" == "/" ]] || [[ -z "$TESTROOT" ]]; then
      echo "$TESTROOT is broken while was testing and won't be deleted"
      exit 1
  fi

  umount $TESTROOT/proc
  umount $TESTROOT/etc/resolv.conf
  umount $TESTROOT/etc/apt/sources.list

  echo "rm -rf $TESTROOT"
  rm -rf $TESTROOT
}

trap ctrl_c INT
function ctrl_c() {
    echo "** Test aborted by CTRL-C"
    __clean_up_testroot
    exit 1
}

debootstrap --variant=buildd --arch amd64 $RELVER $TESTROOT $RELURL

__setup_testroot

chroot $TESTROOT apt-get update -y
for DEP in $DEPS_LIST; do
  chroot $TESTROOT apt-get install -y $DEP
done
chroot $TESTROOT locale-gen en_GB.UTF-8

mkdir -p $SS_DIR

cp -r $DIRA/../serverscope_benchmark $SS_DIR
cp -r $DIRA/../setup.py $SS_DIR
cp -r $DIRA/../README.md $SS_DIR

chroot $TESTROOT python3 /tmp/ss_dir/setup.py install

# Do actual test
LC_ALL="C.UTF-8" chroot $TESTROOT python3 -m serverscope_benchmark -e "test-development@broken.com" -p "Plan|HostingP" -i dd,speedtest,download,dd,fio,unixbench
RESULT="$?"

__clean_up_testroot

if [ "$RESULT" -eq "0" ]; then
    echo "TEST PASSED"
    exit 0
else
    echo "TEST FAILED"
    exit 1
fi
