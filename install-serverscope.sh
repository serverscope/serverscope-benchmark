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

__install () {
    installer="$1"
    program="$2"
    $installer install -y "$program"
}

__get_installer () {
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

__update_installer () {
    installer="$1"
    if [ "$installer" == "apt-get" ] || [ "$installer" == "yum" ]; then
        $installer update -y
    else
        echo "Unknown installer"
    fi
}

__failed_to_install_dependencies () {
    echo "Can not install dependencies automatically."
    echo
}

__ensure_python2 () {
    installer="$1"
    which python > /dev/null
    if [ $? -ne 0 ]; then
        if [ "$installer" == "apt-get" ]; then
            __install $installer python-minimal
        elif [ "$installer" == "yum" ]; then
            __install $installer python2
        else
            __failed_to_install_dependencies
        fi
    fi
}

__ensure_pip () {
    which pip > /dev/null
    if [ $? -ne 0 ]; then
        curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
        python get-pip.py
    fi
}

__ensure_virtualenv () {
    which virtualenv > /dev/null
    if [ $? -ne 0 ]; then
        __ensure_pip
        pip install virtualenv
    fi
}


_installer=$(__get_installer)
__ensure_python2 "$_installer"
if [ $? -eq 0 ]; then
    if [ $_update == "yes" ]; then
        __update_installer "$_installer"
    fi

    if [ "$_installer" == "apt-get" ]; then
        __install "$_installer" build-essential
        __install "$_installer" libaio-dev
    elif [ "$_installer" == "yum" ]; then
        __install "$_installer" make
        __install "$_installer" automake
        __install "$_installer" gcc
        __install "$_installer" gcc-c++
        __install "$_installer" kernel-devel
        __install "$_installer" libaio-devel
        __install "$_installer" perl-Time-HiRes
    else
        __failed_to_install_dependencies
    fi

    __ensure_pip

    # optionally create and activate python virtual environment
    if [ $_virtualenv == "yes" ]; then
        __ensure_virtualenv
        serverscope_venv=$(mktemp -d)
        virtualenv "$serverscope_venv"
        # shellcheck source=/dev/null
        source "$serverscope_venv/bin/activate"
    fi

    # install serverscope-benchmark package
    pip install serverscope-benchmark

    # run serverscope_benchmark
    if [ -z "$_plan" ] || [ -z "$_email" ]; then
        echo Run serverscope manually:
        echo
        echo "    python -m serverscope_benchmark -e \"youremail@yourdomain.com\" -p \"Plan\|Hosting provider\""
        echo
    else
        python -m serverscope_benchmark.__main__ -e "$_email" -p "$_plan" -i "$_included_benchmarks"
    fi

    # cleanup
    if [ $_cleanup == "yes" ]; then
        if [ $_virtualenv == "yes" ]; then
            # delete virtual environment
            rm -rf "$serverscope_venv"
        else
            # uninstall globally installed package
            pip uninstall --yes serverscope-benchmark
        fi
    fi
else
    __failed_to_install_dependencies
fi
