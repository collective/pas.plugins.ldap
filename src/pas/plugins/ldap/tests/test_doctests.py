# -*- coding: utf-8 -*-
from pas.plugins.ldap.testing import PASLDAPLayer
from plone.testing import layered
from plone.testing import z2

import doctest
import pprint
import re
import six
import unittest


optionflags = doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS
optionflags = optionflags | doctest.REPORT_ONLY_FIRST_FAILURE


class Py23DocChecker(doctest.OutputChecker):
    def check_output(self, want, got, optionflags):
        if want != got and six.PY2:
            # if running on py2, ignore any "u" prefixes in the output
            got = re.sub("(\\W|^)u'(.*?)'", "\\1'\\2'", got)
            got = re.sub('(\\W|^)u"(.*?)"', '\\1"\\2"', got)
            # also ignore "b" prefixes in the expected output
            want = re.sub("b'(.*?)'", "'\\1'", want)
            # we get 'ldap.' prefixes on python 3, e.g.
            # ldap.UNWILLING_TO_PERFORM
            want = want.lstrip("ldap.")
        return doctest.OutputChecker.check_output(self, want, got, optionflags)


TESTFILES = [("../properties.rst", PASLDAPLayer), ("../cache.rst", PASLDAPLayer)]


def test_suite():
    suite = unittest.TestSuite()
    suite.addTests(
        [
            layered(
                doctest.DocFileSuite(
                    docfile,
                    globs={"pprint": pprint.pprint, "z2": z2},
                    optionflags=optionflags,
                    checker=Py23DocChecker(),
                ),
                layer=layer(),
            )
            for docfile, layer in TESTFILES
        ]
    )
    return suite
