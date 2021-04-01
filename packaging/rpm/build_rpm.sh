#!/bin/bash

# universal el7/el8 package builder script


if [ "$#" -eq 1 ]; then
  if [ "$1" == "8" -o "$1" == "7" ];then
    DISTRO="el$1"
    VERSION=$1
  else
    echo "Invalid distro: $1, must be 7 or 8"
    exit 1
  fi
else
  source /etc/os-release
  DISTRO="el$VERSION"
fi

echo "Building for version $DISTRO"

sudo yum install python3-setuptools mock -y

DIRA=$(dirname "$0")

pushd $DIRA/../../
  rm -rf dist/
  python3 setup.py sdist
  pushd dist/
    mkdir {SPECS,SOURCES}
    cp ./serverscope_benchmark*tar.gz SOURCES/
    cp ../packaging/rpm/python*spec.$DISTRO SPECS/
    NORM_SPEC=$(ls ./SPECS/*spec.$DISTRO)
    NORM_SPEC=${NORM_SPEC%.$DISTRO}
    mv SPECS/*spec.$DISTRO $NORM_SPEC
    sudo mock -r epel-$VERSION-x86_64 --resultdir ./ --source SOURCES/ --spec SPECS/*.spec
    cp ./*noarch.rpm ../
    echo "Built: $(ls ./*noarch.rpm)"
  popd
popd
