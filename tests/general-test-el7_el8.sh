#!/bin/bash

if [ `whoami` != 'root' ]; then
   echo "You must be root to run tests"
   exit 1
fi

source /etc/os-release
RELVER=$VERSION

if [ "$(pwd)" == "/" ]; then
    echo "It's prohibided to be run from system root (/)!"
    exit 1
fi

TESTROOT=$(pwd)/testroot-el$RELVER/
SS_DIR=$TESTROOT/tmp/ss_dir
RESULT="1"
DEPS_LIST="system-release epel-release basesystem curl python3 python3-setuptools perl make gcc fio"
DIRA=$(dirname "$0")

function __setup_testroot() {
    mount --bind /proc $TESTROOT/proc

    chroot $TESTROOT mknod -m 622 /dev/console c 5 1
    chroot $TESTROOT mknod -m 666 /dev/null c 1 3
    chroot $TESTROOT mknod -m 666 /dev/zero c 1 5
    chroot $TESTROOT mknod -m 666 /dev/ptmx c 5 2
    chroot $TESTROOT mknod -m 666 /dev/tty c 5 0
    chroot $TESTROOT mknod -m 444 /dev/random c 1 8
    chroot $TESTROOT mknod -m 444 /dev/urandom c 1 9
    chroot $TESTROOT chown -v root:tty /dev/{console,ptmx,tty}

    # TODO: ugly code
    # but just for networking
    # but anyway, ro mode, should be safe
    mount --bind -o ro /etc/ $TESTROOT/etc/
}

function __clean_up_testroot() {
  # clean up
  if [[ "$TESTROOT" == "/" ]] || [[ -z "$TESTROOT" ]]; then
      echo "$TESTROOT is broken while was testing and won't be deleted"
      exit 1
  fi

  umount $TESTROOT/proc
  umount $TESTROOT/etc/

  echo "rm -rf $TESTROOT"
  rm -rf $TESTROOT
}

trap ctrl_c INT
function ctrl_c() {
    # to prevent SIGPIPE for broken pipe's stdout
    exec &>$(tty)
    echo "** Test aborted by CTRL-C"
    __clean_up_testroot
    exit 1
}

yum install -y --setopt=releasever=$RELVER --installroot $TESTROOT $DEPS_LIST

__setup_testroot

mkdir -p $SS_DIR
cp -r $DIRA/../serverscope_benchmark $SS_DIR
cp -r $DIRA/../setup.py $SS_DIR
cp -r $DIRA/../README.md $SS_DIR

chroot $TESTROOT python3 /tmp/ss_dir/setup.py install

# Do actual test
LC_ALL="C.UTF-8" chroot $TESTROOT python3 -m serverscope_benchmark -e "test-development@broken.com" -p "Plan|HostingP" -i speedtest,download,dd,fio,unixbench
RESULT="$?"

__clean_up_testroot

if [ "$RESULT" -eq "0" ]; then
    echo "TEST PASSED"
    exit 0
else
    echo "TEST FAILED"
    exit 1
fi
