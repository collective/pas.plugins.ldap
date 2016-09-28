# -*- coding: utf-8 -*-
from interlude import interact
from pas.plugins.ldap.testing import PASLDAPLayer
from plone.testing import layered
from plone.testing import z2
import doctest
import pprint
import unittest


optionflags = doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS
optionflags = optionflags | doctest.REPORT_ONLY_FIRST_FAILURE


TESTFILES = [
    ('properties.rst', PASLDAPLayer),
    ('plugin.rst',     PASLDAPLayer),
    ('cache.rst',      PASLDAPLayer),
]


def test_suite():
    suite = unittest.TestSuite()
    suite.addTests([
        layered(
            doctest.DocFileSuite(
                docfile,
                globs={
                    'interact': interact,
                    'pprint': pprint.pprint,
                    'z2': z2,
                },
                optionflags=optionflags,
            ),
            layer=layer(),
        ) for docfile, layer in TESTFILES
    ])
    return suite
