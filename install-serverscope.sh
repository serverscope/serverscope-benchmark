#!/bin/bash

# Installs serverscope dependencies

# process command line switches
_update=no
_virtualenv=no
_email=
_plan=
_included_benchmarks=

while getopts "uve:p:i:" opt; do
    case $opt in
        u) _update=yes;;
        v) _virtualenv=yes;;
        e) _email=$OPTARG;;
        p) _plan=$OPTARG;;
        i) _included_benchmarks=$OPTARG;;
    esac
done
shift $((OPTIND - 1))

install () {
    installer="$1"
    program="$2"

    which "$program" > /dev/null && return

    echo "Installing $program"
    $installer install -y "$program"
}

get_installer () {
    which yum > /dev/null && installer="yum"
    which apt-get > /dev/null && installer="apt-get"

    # detect OpenSuse, Arch, etc

    echo $installer
}

update_installer () {
    installer="$1"
    if [ "$installer" == "apt-get" ] || [ "$installer" == "yum" ]; then
        $installer update -y
    else
        echo "Unknown installer"
    fi
}

installer=$(get_installer)
if [ $_update == "yes" ]; then
    update_installer "$installer"
fi

if [ "$installer" == "apt-get" ]; then
    install "$installer" python3 python3-pip
    install "$installer" build-essential libaio-dev

    if [ $_virtualenv == "yes" ]; then
        install "$installer" python-virtualenv
    fi
elif [ "$installer" == "yum" ]; then
    install "$installer" make automake gcc gcc-c++ kernel-devel libaio-devel perl-Time-HiRes
else
    echo "Can not install dependencies automatically."
    echo "Please ensure you have Python3 and pip installed."
fi

if [ $_virtualenv == "yes" ]; then
    # create and activate python virtual environment
    serverscope_venv=$(mktemp -d)
    virtualenv "$serverscope_venv"
    # shellcheck source=/dev/null
    source "$serverscope_venv/bin/activate"
fi

echo pip install serverscope
[ -n "$_included_benchmarks" ] && included_benchmarks="-i $_included_benchmarks"
if [ -z "$_plan" ] || [ -z "$_email" ]; then
    echo Run serverscope manually: python -m serverscope -e \"youremail@yourdomain.com\" -p \"Plan\|Hosting provider\"
else
    echo serverscope.py -e "$_email" -p "$_plan" "$included_benchmarks"
fi

if [ $_virtualenv == "yes" ]; then
    # cleanup virtual environment
    rm -rf "$serverscope_venv"
fi
