# Copyright (c) 2006-2009 by BlueDynamics Alliance, Austria
# GNU General Public License (GPL)

import os, sys

if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

import code
import unittest
from zope.testing import doctest
from Testing.ZopeTestCase import ZopeDocFileSuite
from Products.PloneTestCase import PloneTestCase

import Products
from Products.Five import zcml

PloneTestCase.installProduct('PluginRegistry')
PloneTestCase.installProduct('PluggableAuthService')
PloneTestCase.installProduct('PlonePAS')
PloneTestCase.installProduct('PasswordResetTool')
PloneTestCase.installProduct('PASGroupsFromLDAP')
PloneTestCase.installProduct('Five')

ZCMLS = (
    Products.PASGroupsFromLDAP,
    )

for package in ZCMLS:
    zcml.load_config('configure.zcml', package=package)

PloneTestCase.setupPloneSite(products=['PlonePAS'])

def interact(self, locals=None):
    """Provides an interactive shell aka console inside your testcase.

    It looks exact like in a doctestcase and you can copy and paste
    code from the shell into your doctest. The locals in the testcase are
    available, becasue you are in the testcase.

    In your testcase or doctest you can invoke the shell at any point by
    calling::

        >>> self.interact( locals() )

    locals -- passed to InteractiveInterpreter.__init__()
    """
    savestdout = sys.stdout
    sys.stdout = sys.stderr
    sys.stderr.write('='*70)
    console = code.InteractiveConsole(locals)
    console.interact("""
ZopeTestCase Interactive Console
(c) BlueDynamics Alliance, Austria - 2005

Note: You have the same locals available as in your test-case.
""")
    sys.stdout.write('\nend of ZopeTestCase Interactive Console session\n')
    sys.stdout.write('='*70+'\n')
    sys.stdout = savestdout
    
PloneTestCase.PloneTestCase.interact = interact

def test_suite():
    testsuite = unittest.TestSuite((
        ZopeDocFileSuite('propertiesplugin.txt',
                         package='Products.PASGroupsFromLDAP.docs',
                         test_class=PloneTestCase.PloneTestCase,
                         optionflags=doctest.ELLIPSIS|doctest.REPORT_ONLY_FIRST_FAILURE),
    ))
    return testsuite

if __name__ == '__main__':
    framework()

