#!/bin/bash

# Installs serverscope

CENTOS8_PKG="https://serverscope.io/packages/rpm/python3-serverscope_benchmark-2.0.1-1.el8.noarch.rpm"
CENTOS7_PKG="https://serverscope.io/packages/rpm/python36-serverscope_benchmark-2.0.1-1.el7.noarch.rpm"
DEB_PKG="https://serverscope.io/packages/deb/python3-serverscope-benchmark_2.0.1-1_all.deb"
UBUNTU_16_04_DEP="https://serverscope.io/packages/deb/python3-distro_1.0.1-2_all.deb"

# process command line switches
_email=
_plan=
_included_benchmarks=all

while getopts "e:p:i:" opt; do
    case $opt in
        e) _email=$OPTARG;;
        p) _plan=$OPTARG;;
        i) _included_benchmarks=$OPTARG;;
    esac
done
shift $((OPTIND - 1))

__install_deb_url() {
    PKGS=""
    apt update -y
    for x in $@; do
        TEMP_DEB="$(mktemp --suffix ".deb")"
        wget -O "$TEMP_DEB" $x
        chmod 444 $TEMP_DEB
        PKGS="$PKGS $TEMP_DEB"
    done
    apt install -y $PKGS
    rm -f "$PKGS"
}

SS_BENCH_CMD="LC_ALL=\"C.UTF-8\" python3 -m serverscope_benchmark -e \"$_email\" -p \"$_plan\" -i \"$_included_benchmarks\""

source /etc/os-release
if [ "$NAME" == "CentOS Linux" ]; then
    echo "Detected $NAME"
    if [ "$VERSION_ID" == "8" ]; then
        dnf install -y $CENTOS8_PKG
    elif [ "$VERSION_ID" == "7" ]; then
        yum install -y epel-release
        yum install -y $CENTOS7_PKG
    else
        echo "Only packages for CentOS Linux 7/8 are available for installation"
        exit 1
    fi
elif [ "$NAME" == "Ubuntu" ]; then
    echo "Detected $NAME"
    if [ "$VERSION_CODENAME" == "xenial" ]; then
        __install_deb_url $UBUNTU_16_04_DEP $DEB_PKG
    elif [ "$VERSION_CODENAME" == "bionic" ] || \
         [ "$VERSION_CODENAME" == "focal" ] || \
         [ "$VERSION_CODENAME" == "groovy" ]; then
        __install_deb_url $DEB_PKG
    else
        echo "Only packages for Ubuntu 16.04/18.04/20.04/20.10 are available for installation"
        exit 1
    fi
elif [ "$NAME" == "Debian GNU/Linux" ]; then
    if [ "$VERSION_ID" == "9" ] || \
       [ "$VERSION_ID" == "10" ]; then
        __install_deb_url $DEB_PKG
    else
        echo "Only packages for Debian 9/10 are available for installation"
        exit 1
    fi
else
    echo "Your distro $NAME $VERSION_ID currently is not supported by script"
    echo "You might manually install [gcc, make, perl, python3 >= 3.5, curl, python3-setuptools, fio] + 'pip3 install serverscope-benchmark'"
    echo "And run: '$SS_BENCH_CMD'"
    exit 1
fi

# run serverscope_benchmark
if [ -z "$_plan" ] || [ -z "$_email" ]; then
    echo Run serverscope manually:
    echo
    echo " LC_ALL=\"C.UTF-8\" python3 -m serverscope_benchmark -e \"youremail@yourdomain.com\" -p \"Plan\|Hosting provider\""
    echo
else
    bash -c "$SS_BENCH_CMD"
fi

exit 0
