#!/bin/bash

# Installs serverscope dependencies

# process command line switches
_update=no
_virtualenv=no
_cleanup=no
_email=
_plan=
_included_benchmarks=all

while getopts "uvce:p:i:" opt; do
    case $opt in
        u) _update=yes;;
        v) _virtualenv=yes;;
        c) _cleanup=yes;;
        e) _email=$OPTARG;;
        p) _plan=$OPTARG;;
        i) _included_benchmarks=$OPTARG;;
    esac
done
shift $((OPTIND - 1))

install () {
    installer="$1"
    program="$2"
    $installer install -y "$program"
}

get_installer () {
    installer=unknown
    which yum > /dev/null && installer="yum"
    which apt-get > /dev/null && installer="apt-get"

    # TODO detect OpenSuse, Arch, etc

    if [ $installer != "unknown" ]; then
        echo $installer
    else
        return 1
    fi
}

update_installer () {
    installer="$1"
    if [ "$installer" == "apt-get" ] || [ "$installer" == "yum" ]; then
        $installer update -y
    else
        echo "Unknown installer"
    fi
}

__failed_to_install_dependencies () {
    echo "Can not install dependencies automatically."
    echo "Please ensure you have Python3 installed."
    echo
}


installer=$(get_installer)
if [ $? -eq 0 ]; then
    if [ $_update == "yes" ]; then
        update_installer "$installer"
    fi

    if [ "$installer" == "apt-get" ]; then
        install "$installer" python3
        install "$installer" python3-pip
        install "$installer" python3-venv
        if [ $? -ne 0 ]; then
            # This is a fix for Ubuntu 14.04 bug
            # https://bugs.launchpad.net/ubuntu/+source/python3.4/+bug/1532231
            install "$installer" python3.4-venv
        fi
        install "$installer" build-essential
        install "$installer" libaio-dev
    elif [ "$installer" == "yum" ]; then
        install "$installer" make
        install "$installer" automake
        install "$installer" gcc
        install "$installer" gcc-c++
        install "$installer" kernel-devel
        install "$installer" libaio-devel
        install "$installer" perl-Time-HiRes
        install "$installer" epel-release
        install "$installer" python34
        install "$installer" python34-setuptools
        easy_install-3.4 pip
    else
        __failed_to_install_dependencies
    fi

    # optionally create and activate python virtual environment
    if [ $_virtualenv == "yes" ]; then
        serverscope_venv=$(mktemp -d)
        python3 -m venv "$serverscope_venv"
        # shellcheck source=/dev/null
        source "$serverscope_venv/bin/activate"
    fi

    # install serverscope-benchmark package
    python3 -m pip install serverscope-benchmark

    # run serverscope_benchmark
    if [ -z "$_plan" ] || [ -z "$_email" ]; then
        echo Run serverscope manually:
        echo
        echo "    python3 -m serverscope_benchmark -e \"youremail@yourdomain.com\" -p \"Plan\|Hosting provider\""
        echo
    else
        python3 -m serverscope_benchmark -e "$_email" -p "$_plan" -i "$_included_benchmarks"
    fi

    # cleanup
    if [ $_cleanup == "yes" ]; then
        if [ $_virtualenv == "yes" ]; then
            # delete virtual environment
            rm -rf "$serverscope_venv"
        else
            # uninstall globally installed package
            python3 -m pip uninstall --yes serverscope-benchmark
        fi
    fi
else
    __failed_to_install_dependencies
fi
