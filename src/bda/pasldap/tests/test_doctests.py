import unittest
import doctest
from Testing import ZopeTestCase
from Products.PloneTestCase import ptc

from bda.plone.ldap import testing

from pprint import pprint
from interlude import interact

optionflags = (doctest.NORMALIZE_WHITESPACE|
               doctest.ELLIPSIS|
               doctest.REPORT_NDIFF)

def test_suite():
    suite = ZopeTestCase.FunctionalDocFileSuite(
            # the files to test
            optionflags=optionflags,
            globs={'interact': interact,
                   'pprint': pprint,},
            test_class=testing.LDAPTestCase)
    suite.layer = testing.ldap_integration_layer
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
