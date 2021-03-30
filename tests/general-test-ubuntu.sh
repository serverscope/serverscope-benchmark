#!/bin/bash


cat /etc/os-release | grep 'Ubuntu' > /dev/null
if [ $? -ne 0 ]; then
    echo "Test is intended to be run on Ubuntu, exiting"
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
TESTROOT=$(pwd)/testroot-$RELVER/
SS_DIR=$TESTROOT/tmp/ss_dir
RESULT="1"
DEPS_LIST="make perl fio gcc python3-setuptools python3-distro python3-requests curl locales"

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

debootstrap --variant=buildd --arch amd64 $UBUNTU_CODENAME $TESTROOT http://archive.ubuntu.com/ubuntu/

__setup_testroot

chroot $TESTROOT apt-get update -y
for DEP in $DEPS_LIST; do
  chroot $TESTROOT apt-get install -y $DEP
done
chroot $TESTROOT locale-gen en_GB.UTF-8

mkdir -p $SS_DIR
cp -r ../serverscope_benchmark $SS_DIR
cp -r ../setup.py $SS_DIR
cp -r ../README.md $SS_DIR

chroot $TESTROOT python3 /tmp/ss_dir/setup.py install

# Do actual test
chroot $TESTROOT python3 -m serverscope_benchmark -e "test-development@broken.com" -p "Plan|HostingP" -i speedtest,download,dd,fio,unixbench
RESULT="$?"

__clean_up_testroot

if [ "$RESULT" -eq "0" ]; then
    echo "TEST PASSED"
    exit 0
else
    echo "TEST FAILED"
    exit 1
fi
