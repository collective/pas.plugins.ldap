# -*- coding: utf-8 -*-
from pas.plugins.ldap.testing import PASLDAPLayer
from plone.browserlayer.utils import registered_layers

import unittest


class InstallTestCase(unittest.TestCase):

    layer = PASLDAPLayer

    def setUp(self):
        self.portal = self.layer['portal']
        self.qi = self.portal['portal_quickinstaller']

    def test_installed(self):
        self.assertTrue(self.qi.isProductInstalled('pas.plugins.ldap'))

    def test_addon_layer(self):
        layers = [l.getName() for l in registered_layers()]
        self.assertIn('ILDAPPlugin', layers)

    def test_pas_plugin(self):
        acl_users = self.portal.acl_users
        self.assertIn('pasldap', acl_users.objectIds())


class UninstallTestCase(unittest.TestCase):

    layer = PASLDAPLayer

    def setUp(self):
        self.portal = self.layer['portal']
        self.qi = self.portal['portal_quickinstaller']
        self.qi.uninstallProducts(products=['pas.plugins.ldap'])

    def test_uninstalled(self):
        self.assertFalse(self.qi.isProductInstalled('pas.plugins.ldap'))

    def test_addon_layer_removed(self):
        layers = [l.getName() for l in registered_layers()]
        self.assertNotIn('ILDAPPlugin', layers)

    def test_pas_plugin_removed(self):
        acl_users = self.portal.acl_users
        self.assertNotIn('pasldap', acl_users.objectIds())
