#!/bin/bash

cd $1

./configure --with-tls --enable-slapd=yes --enable-overlays CPPFLAGS=-D_GNU_SOURCE --prefix=$2
make clean
make depend
make -j4
make install

cd -