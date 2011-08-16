import unittest
import doctest
import pprint
from interlude import interact
from plone.testing import layered
from .testing import PASLDAPLayer

optionflags = doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS

TESTFILES = ['_plugin.txt']

def test_suite():
    suite = unittest.TestSuite()
    suite.addTests([
            layered(
                doctest.DocFileSuite(
                    docfile,
                    globs={'interact': interact,
                           'pprint': pprint.pprint,
                           },
                    optionflags=optionflags,
                    ),
                layer=PASLDAPLayer(),
                )
            for docfile in TESTFILES
            ])
    return suite