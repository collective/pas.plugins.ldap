"""Unit tests for pas.plugins.ldap."""

from testing import PASLDAP_FIXTURE
from Products.PlonePAS.plugins.ufactory import PloneUser
from unittest.mock import MagicMock

import unittest


class TestInitialize(unittest.TestCase):
    """Tests for the initialize() function in __init__.py."""

    def test_initialize_registers_plugin(self):
        """initialize() calls registerMultiPlugin and registerClass."""
        from pas.plugins.ldap import initialize
        from pas.plugins.ldap.plugin import LDAPPlugin

        context = MagicMock()
        initialize(context)

        context.registerClass.assert_called_once()
        call_kwargs = context.registerClass.call_args
        self.assertIs(call_kwargs[0][0], LDAPPlugin)


class TestPluginInit(unittest.TestCase):
    """Tests for the initialization of the LDAPPlugin."""
    layer = PASLDAP_FIXTURE

    @property
    def pas(self):
        """Helper to get the PAS from the test layer."""
        return self.layer["app"].acl_users

    def test_pas_installed(self):
        """Test that the PAS is installed."""
        from Products.PluggableAuthService.PluggableAuthService import (
            PluggableAuthService,
        )

        self.assertIsInstance(self.pas, PluggableAuthService)

    def test_create(self):
        """Creating the plugin adds it to the PAS."""
        from pas.plugins.ldap.setuphandlers import _addPlugin

        _addPlugin(self.pas)
        self.assertIn("pasldap", self.pas.objectIds())


class TestPluginFeatures(unittest.TestCase):
    """Tests for the features of the LDAPPlugin."""
    layer = PASLDAP_FIXTURE

    @property
    def pas(self):
        """Helper to get the PAS from the test layer."""
        return self.layer["app"].acl_users

    def setUp(self):
        """Set up the test by adding the LDAP plugin to the PAS and configuring it."""
        # add plugin
        from pas.plugins.ldap.setuphandlers import _addPlugin

        _addPlugin(self.pas)
        self.ldap = self.pas["pasldap"]

        # turn off plugin_caching for testing,
        # otherwise test request has some strange behaviour:
        self.ldap.plugin_caching = False

        self.ldap.users.principal_attrmap["fullname"] = "cn"
        self.ldap.groups.principal_attrmap["title"] = "cn"

    def test_IAuthenticationPlugin(self):
        """Test the IAuthenticationPlugin implementation."""
        self.assertEqual(
            self.ldap.authenticateCredentials({"login": "cn0", "password": "secret0"}),
            ("uid0", "cn0"),
        )

        self.assertIsNone(
            self.ldap.authenticateCredentials({"login": "admin", "password": "admin"})
        )

        self.assertIsNone(
            self.ldap.authenticateCredentials(
                {"login": "nonexist", "password": "dummy"}
            )
        )

    def test_IGroupEnumerationPlugin_id(self):
        """Test the IGroupEnumerationPlugin implementation with id criteria."""
        self.assertEqual(
            [sorted(group.items()) for group in self.ldap.enumerateGroups(id="group2")],
            [[("id", "group2"), ("pluginid", "pasldap")]],
        )
        self.assertEqual(
            sorted(_["id"] for _ in self.ldap.enumerateGroups(id="group*")),
            [
                "group0",
                "group1",
                "group2",
                "group3",
                "group4",
                "group5",
                "group6",
                "group7",
                "group8",
                "group9",
            ],
        )
        self.assertEqual(
            [_["id"] for _ in self.ldap.enumerateGroups(id="group*", sort_by="id")],
            [
                "group0",
                "group1",
                "group2",
                "group3",
                "group4",
                "group5",
                "group6",
                "group7",
                "group8",
                "group9",
            ],
        )
        self.assertEqual(self.ldap.enumerateGroups(id="group*", exact_match=True), ())
        self.assertEqual(
            [
                sorted(group.items())
                for group in self.ldap.enumerateGroups(id="group5", exact_match=True)
            ],
            [[("id", "group5"), ("pluginid", "pasldap")]],
        )
        self.assertEqual(len(self.ldap.enumerateGroups(id="group*", max_results=3)), 3)

    def test_IGroupEnumerationPlugin_title(self):
        """Test the IGroupEnumerationPlugin implementation with title criteria."""
        self.assertEqual(
            [
                sorted(group.items())
                for group in self.ldap.enumerateGroups(title="group2")
            ],
            [[("id", "group2"), ("pluginid", "pasldap")]],
        )
        self.assertEqual(
            len(self.ldap.enumerateGroups(title="group*", max_results=3)), 3
        )

    def test_IGroupsPlugin_without_memberOf_support(self):
        """Test the IGroupsPlugin implementation without memberOf support."""
        user = self.pas.getUserById("uid9")
        self.assertEqual(self.ldap.getGroupsForPrincipal(user), ["group9"])

        user = self.pas.getUserById("uid1")
        self.assertEqual(
            self.ldap.getGroupsForPrincipal(user),
            [
                "group1",
                "group2",
                "group3",
                "group4",
                "group5",
                "group6",
                "group7",
                "group8",
                "group9",
            ],
        )

        user = self.pas.getUserById("uid0")
        self.assertEqual(self.ldap.getGroupsForPrincipal(user), [])

    def test_IGroupsPlugin_with_memberOf_support(self):
        """Test the IGroupsPlugin implementation with memberOf support."""
        self.ldap.users.parent.ucfg.memberOfSupport = True
        user = self.pas.getUserById("uid9")
        self.assertEqual(self.ldap.getGroupsForPrincipal(user), ["group9"])

        user = self.pas.getUserById("uid1")
        self.assertEqual(
            self.ldap.getGroupsForPrincipal(user),
            [
                "group1",
                "group2",
                "group3",
                "group4",
                "group5",
                "group6",
                "group7",
                "group8",
                "group9",
            ],
        )

        user = self.pas.getUserById("uid0")
        self.assertEqual(self.ldap.getGroupsForPrincipal(user), [])
        self.ldap.users.parent.ucfg.memberOfSupport = False

    def test_IUserEnumerationPlugin_with_id(self):
        """Test the IUserEnumerationPlugin implementation with id criteria."""
        self.assertEqual(
            [sorted(user.items()) for user in self.ldap.enumerateUsers(id="uid1")],
            [[("id", "uid1"), ("login", "cn1"), ("pluginid", "pasldap")]],
        )
        self.assertEqual(
            [sorted(user.items()) for user in self.ldap.enumerateUsers(id="uid*")],
            [
                [("id", "uid0"), ("login", "cn0"), ("pluginid", "pasldap")],
                [("id", "uid1"), ("login", "cn1"), ("pluginid", "pasldap")],
                [("id", "uid2"), ("login", "cn2"), ("pluginid", "pasldap")],
                [("id", "uid3"), ("login", "cn3"), ("pluginid", "pasldap")],
                [("id", "uid4"), ("login", "cn4"), ("pluginid", "pasldap")],
                [("id", "uid5"), ("login", "cn5"), ("pluginid", "pasldap")],
                [("id", "uid6"), ("login", "cn6"), ("pluginid", "pasldap")],
                [("id", "uid7"), ("login", "cn7"), ("pluginid", "pasldap")],
                [("id", "uid8"), ("login", "cn8"), ("pluginid", "pasldap")],
                [("id", "uid9"), ("login", "cn9"), ("pluginid", "pasldap")],
            ],
        )
        self.assertEqual(
            [_["id"] for _ in self.ldap.enumerateUsers(id="uid*", sort_by="id")],
            [
                "uid0",
                "uid1",
                "uid2",
                "uid3",
                "uid4",
                "uid5",
                "uid6",
                "uid7",
                "uid8",
                "uid9",
            ],
        )
        self.assertEqual(self.ldap.enumerateUsers(id="uid*", exact_match=True), ())

        self.assertEqual(
            [
                sorted(user.items())
                for user in self.ldap.enumerateUsers(id="uid4", exact_match=True)
            ],
            [[("id", "uid4"), ("login", "cn4"), ("pluginid", "pasldap")]],
        )
        self.assertEqual(len(self.ldap.enumerateUsers(id="uid*", max_results=3)), 3)

    def test_IUserEnumerationPlugin_with_login(self):
        """Test the IUserEnumerationPlugin implementation with login criteria."""
        users = self.ldap.enumerateUsers(login="cn1")
        self.assertEqual(
            [sorted(user.items()) for user in users],
            [[("id", "uid1"), ("login", "cn1"), ("pluginid", "pasldap")]],
        )

    def test_IUserEnumerationPlugin_with_fullname(self):
        """Test the IUserEnumerationPlugin implementation with fullname criteria."""
        users = self.ldap.enumerateUsers(fullname="cn1")
        self.assertEqual(
            [sorted(user.items()) for user in users],
            [[("id", "uid1"), ("login", "cn1"), ("pluginid", "pasldap")]],
        )
        users = self.ldap.enumerateUsers(fullname="cn*")
        self.assertEqual(len(users), 10)

    def test_IDeleteCapability(self):
        """It's not allowed to delete a principal using this plugin.
        We may change this later and make it configurable
        """
        self.assertFalse(self.ldap.allowDeletePrincipal("uid0"))
        self.assertFalse(self.ldap.allowDeletePrincipal("unknownuser"))

    def test_pickable_propertysheet(self):
        """In order to cache propertysheets it must be picklable"""
        from Acquisition import aq_base

        import pickle

        self.assertGreater(len(pickle.dumps(aq_base(self.ldap))), 170)

    def test_IGroupCapability(self):
        """By now adding groups is not allowed.
        We may change this later and make it configurable.
        """
        self.assertFalse(self.ldap.allowGroupAdd("uid0", "group0"))
        self.assertFalse(self.ldap.allowGroupRemove("uid0", "group0"))

    def test_IGroupIntrospection_getGroupById(self):
        """getGroupById returns the portal_groupdata-ish object for a group
        corresponding to this id
        """
        from Products.PlonePAS.plugins.group import PloneGroup

        self.assertIsInstance(self.ldap.getGroupById("group0"), PloneGroup)
        self.assertEqual(self.ldap.getGroupById("group0").getId(), "group0")
        self.assertIsNone(self.ldap.getGroupById("non-existent"))

    def test_IGroupIntrospection_getGroupIds(self):
        """getGroupIds returns the list of all group ids."""
        self.assertEqual(
            self.ldap.getGroupIds(),
            [
                "group0",
                "group1",
                "group2",
                "group3",
                "group4",
                "group5",
                "group6",
                "group7",
                "group8",
                "group9",
            ],
        )

    def test_IGroupIntrospection_getGroups(self):
        """getGroups returns the list of all group objects."""
        groups = self.ldap.getGroups()
        self.assertEqual(len(groups), 10)
        from Products.PlonePAS.plugins.group import PloneGroup

        self.assertIsInstance(groups[0], PloneGroup)

    def test_IGroupIntrospection_getGroupMembers(self):
        """getGroupMembers returns the list of all group members."""
        self.assertEqual(self.ldap.getGroupMembers("group3"), ("uid1", "uid2", "uid3"))

    def test_IPasswordSetCapability(self):
        """Test the IPasswordSetCapability implementation."""
        # users may set passwords
        self.assertTrue(self.ldap.allowPasswordSet("uid0"))
        # groups not
        self.assertFalse(self.ldap.allowPasswordSet("group0"))
        # also so for non existent
        self.assertFalse(self.ldap.allowPasswordSet("ghost"))

    def test_IGroupManagement(self):
        """Test the IGroupManagement implementation."""
        self.assertFalse(self.ldap.addGroup(id))
        self.assertFalse(self.ldap.addPrincipalToGroup("uid0", "group0"))
        self.assertFalse(self.ldap.updateGroup("group9", **{}))
        self.assertFalse(self.ldap.setRolesForGroup("uid0", roles=("Manager")))
        self.assertFalse(self.ldap.removeGroup("group0"))
        self.assertFalse(self.ldap.removePrincipalFromGroup("uid1", "group1"))

    def test_IMutablePropertiesPlugin_get(self):
        """Test the IMutablePropertiesPlugin implementation."""
        user = self.pas.getUserById("uid0")
        sheet = self.ldap.getPropertiesForUser(user, request=None)
        from pas.plugins.ldap.sheet import LDAPUserPropertySheet

        self.assertIsInstance(sheet, LDAPUserPropertySheet)
        self.assertEqual(sheet.getProperty("mail"), "uid0@groupOfNames_10_10.com")

    def test_IMutablePropertiesPlugin_set(self):
        """Test the IMutablePropertiesPlugin implementation.
        Set does nothing, but the sheet itselfs set immediatly."""
        user = self.pas.getUserById("uid0")
        from pas.plugins.ldap.sheet import LDAPUserPropertySheet

        sheet = LDAPUserPropertySheet(user, self.ldap)
        self.assertEqual(sheet.getProperty("mail"), "uid0@groupOfNames_10_10.com")
        sheet.setProperty(None, "mail", "foobar@example.com")
        self.assertEqual(sheet.getProperty("mail"), "foobar@example.com")
        sheet2 = LDAPUserPropertySheet(user, self.ldap)
        self.assertEqual(sheet2.getProperty("mail"), "foobar@example.com")

    def test_IMutablePropertiesPlugin_pickle(self):
        """Test that the property sheet is picklable, which is required for caching."""
        user = self.pas.getUserById("uid0")
        from pas.plugins.ldap.sheet import LDAPUserPropertySheet

        sheet = LDAPUserPropertySheet(user, self.ldap)
        import pickle

        self.assertGreater(len(pickle.dumps(sheet)), 600)

    def test_IUserManagement(self):
        """Test the IUserManagement implementation."""
        self.ldap.doChangeUser("uid9", "geheim")
        self.assertEqual(
            self.ldap.authenticateCredentials({"login": "cn9", "password": "geheim"}),
            ("uid9", "cn9"),
        )
        # no delete support:
        self.assertFalse(self.ldap.doDeleteUser("uid0"))

    def test_IRolesPlugin(self):
        """Test the IRolesPlugin implementation."""
        ldap_user = PloneUser("uid0", login="cn0")
        self.assertEqual(
            self.ldap.getRolesForPrincipal(ldap_user),
            ("Member",),
        )
        other_user = PloneUser("unknown", login="other")
        self.assertEqual(
            self.ldap.getRolesForPrincipal(other_user),
            (),
        )

    # other tests higher pas level
    def test_user_for_group_without_memberOfSupport(self):
        """Test user group retrieval without memberOf support."""
        user = self.pas.getUserById("uid9")
        self.assertEqual(user.getGroups(), ["group9"])

    def test_user_for_group_with_memberOfSupport(self):
        """Test user group retrieval with memberOf support."""
        self.ldap.users.parent.ucfg.memberOfSupport = True
        user = self.pas.getUserById("uid9")
        self.assertEqual(user.getGroups(), ["group9"])
        self.ldap.users.parent.ucfg.memberOfSupport = False
