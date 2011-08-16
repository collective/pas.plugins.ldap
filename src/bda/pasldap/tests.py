import unittest
import doctest
from interlude import interact
from Testing import ZopeTestCase as ztc
from plone.testing import layered
from node.ext.ldap import testing

optionflags = doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS

class ZopeLDAPTestcase(ztc.ZopeTestCase):



TESTFILES = [('_plugin.txt', testing.LDIF_groupOfNames]

def test_suite():
    suite = unittest.TestSuite()
    suite.addTests([
            layered(
                doctest.DocFileSuite(
                    docfile,
                    globs={'interact': interlude.interact,
                           'pprint': pprint.pprint,
                           'pp': pprint.pprint,
                           },
                    optionflags=optionflags,
                    ),
                layer=layer,
                )
            for docfile, layer in DOCFILES
            ])
    return suite