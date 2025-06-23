from testing import PASLDAPLayer
from plone.testing import layered
from plone.testing import zope

import doctest
import pprint
import re
import six
import unittest


optionflags = doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS
optionflags = optionflags | doctest.REPORT_ONLY_FIRST_FAILURE

TESTFILES = [("properties.rst", PASLDAPLayer), ("cache.rst", PASLDAPLayer)]


def test_suite():
    suite = unittest.TestSuite()
    suite.addTests(
        [
            layered(
                doctest.DocFileSuite(
                    docfile,
                    globs={"pprint": pprint.pprint, "z2": zope},
                    optionflags=optionflags,
                ),
                layer=layer(),
            )
            for docfile, layer in TESTFILES
        ]
    )
    return suite
