#!/bin/sh

# see https://community.plone.org/t/not-using-bootstrap-py-as-default/620
rm -r ./lib ./include ./local ./bin
ln -fs plone-5.2.x.cfg buildout.cfg
virtualenv --clear .
./bin/pip install -r requirements.txt
./bin/buildout
