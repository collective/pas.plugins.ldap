"""Pure unit tests for pas.plugins.ldap.plugin module.

These tests exercise the branches not reached by the LDAP integration
tests, using unittest.mock so no real LDAP server or Zope layer is needed.
"""

import time
import unittest
from unittest.mock import MagicMock, patch, PropertyMock

import ldap

from pas.plugins.ldap.plugin import (
    LDAP_ERROR_LOG_TIMEOUT,
    LDAP_LONG_RUNNING_LOG_THRESHOLD,
    LDAPPlugin,
    ldap_error_handler,
    manage_addLDAPPlugin,
)
from pas.plugins.ldap.interfaces import VALUE_NOT_CACHED
from Products.PluggableAuthService.interfaces import plugins as pas_interfaces
from Products.PlonePAS import interfaces as plonepas_interfaces


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_plugin(plugin_id="testplugin", title="Test Plugin"):
    """Return a minimal LDAPPlugin bypassing Zope/LDAP initialization."""
    from BTrees import OOBTree

    plugin = LDAPPlugin.__new__(LDAPPlugin)
    plugin.id = plugin_id
    plugin.title = title
    plugin.plugin_caching = True
    plugin.settings = OOBTree.OOBTree()
    return plugin


class _Dummy:
    """Simple object without any LDAP/Zope attributes."""


# ---------------------------------------------------------------------------
# manage_addLDAPPlugin  (lines 52-55)
# ---------------------------------------------------------------------------

class TestManageAddLDAPPlugin(unittest.TestCase):
    """Tests for the module-level manage_addLDAPPlugin factory function."""

    def test_adds_plugin_to_dispatcher(self):
        """Creates a plugin and calls dispatcher._setObject (lines 52-53)."""
        dispatcher = MagicMock()
        with patch("pas.plugins.ldap.plugin.LDAPPlugin") as MockPlugin:
            instance = MockPlugin.return_value
            instance.getId.return_value = "myldap"
            manage_addLDAPPlugin(dispatcher, "myldap", "My LDAP")
        dispatcher._setObject.assert_called_once_with("myldap", instance)

    def test_redirects_when_response_given(self):
        """Calls RESPONSE.redirect when RESPONSE is not None (lines 54-55)."""
        dispatcher = MagicMock()
        response = MagicMock()
        with patch("pas.plugins.ldap.plugin.LDAPPlugin") as MockPlugin:
            MockPlugin.return_value.getId.return_value = "myldap"
            manage_addLDAPPlugin(dispatcher, "myldap", RESPONSE=response)
        response.redirect.assert_called_once_with("manage_workspace")

    def test_no_redirect_when_response_is_none(self):
        """No redirect call when RESPONSE is None (line 54 branch)."""
        dispatcher = MagicMock()
        with patch("pas.plugins.ldap.plugin.LDAPPlugin") as MockPlugin:
            MockPlugin.return_value.getId.return_value = "myldap"
            manage_addLDAPPlugin(dispatcher, "myldap", RESPONSE=None)
        dispatcher._setObject.assert_called_once()


# ---------------------------------------------------------------------------
# ldap_error_handler  (lines 93, 102-106)
# ---------------------------------------------------------------------------

class TestLdapErrorHandler(unittest.TestCase):
    """Tests for the ldap_error_handler decorator factory."""

    def test_long_running_call_logs_error(self):
        """When elapsed > threshold, logger.error is called (line 93)."""

        @ldap_error_handler("test_prefix", default=None)
        def slow_op(self):
            return "done"

        obj = _Dummy()  # no _v_ldaperror_timeout attribute
        with patch("pas.plugins.ldap.plugin.process_time") as mock_pt:
            # second call returns a value beyond the threshold
            mock_pt.side_effect = [0.0, LDAP_LONG_RUNNING_LOG_THRESHOLD + 1.0]
            with patch("pas.plugins.ldap.plugin.logger") as mock_logger:
                result = slow_op(obj)
        mock_logger.error.assert_called()
        self.assertEqual(result, "done")

    def test_generic_exception_sets_error_state_and_returns_default(self):
        """Non-LDAPError exception: sets timeout attrs, returns default (102-106)."""

        @ldap_error_handler("test_prefix", default="FALLBACK")
        def bad_op(self):
            raise RuntimeError("something bad")

        obj = _Dummy()
        with patch("pas.plugins.ldap.plugin.logger"):
            result = bad_op(obj)
        self.assertEqual(result, "FALLBACK")
        self.assertEqual(obj._v_ldaperror_msg, "something bad")
        self.assertTrue(hasattr(obj, "_v_ldaperror_timeout"))

    def test_ldap_error_sets_error_state_and_returns_default(self):
        """LDAPError: sets timeout attrs, returns default."""

        @ldap_error_handler("test_prefix", default=None)
        def ldap_op(self):
            raise ldap.LDAPError("LDAP error")

        obj = _Dummy()
        with patch("pas.plugins.ldap.plugin.logger"):
            result = ldap_op(obj)
        self.assertIsNone(result)
        self.assertTrue(hasattr(obj, "_v_ldaperror_msg"))

    def test_timeout_phase_returns_default_immediately(self):
        """When a recent error exists and timeout not expired, returns default."""

        @ldap_error_handler("test_prefix", default="TIMEOUT_FALLBACK")
        def good_op(self):
            return "result"

        obj = _Dummy()
        obj._v_ldaperror_timeout = time.time()   # very recent error
        obj._v_ldaperror_msg = "previous failure"
        with patch("pas.plugins.ldap.plugin.logger"):
            result = good_op(obj)
        self.assertEqual(result, "TIMEOUT_FALLBACK")


# ---------------------------------------------------------------------------
# groups_enabled / users_enabled  (lines 161, 167)
# ---------------------------------------------------------------------------

class TestGroupsUsersEnabled(unittest.TestCase):
    def setUp(self):
        self.plugin = _make_plugin()

    def test_groups_enabled_true_when_groups_not_none(self):
        """groups_enabled returns True when groups property is not None (161)."""
        with patch.object(type(self.plugin), "groups", new_callable=PropertyMock) as pg:
            pg.return_value = MagicMock()
            self.assertTrue(self.plugin.groups_enabled)

    def test_groups_enabled_false_when_groups_is_none(self):
        """groups_enabled returns False when groups property is None (161)."""
        with patch.object(type(self.plugin), "groups", new_callable=PropertyMock) as pg:
            pg.return_value = None
            self.assertFalse(self.plugin.groups_enabled)

    def test_users_enabled_true_when_users_not_none(self):
        """users_enabled returns True when users property is not None (167)."""
        with patch.object(type(self.plugin), "users", new_callable=PropertyMock) as pu:
            pu.return_value = MagicMock()
            self.assertTrue(self.plugin.users_enabled)

    def test_users_enabled_false_when_users_is_none(self):
        """users_enabled returns False when users property is None (167)."""
        with patch.object(type(self.plugin), "users", new_callable=PropertyMock) as pu:
            pu.return_value = None
            self.assertFalse(self.plugin.users_enabled)


# ---------------------------------------------------------------------------
# ldaperror property  (lines 204-208)
# ---------------------------------------------------------------------------

class TestLdaperror(unittest.TestCase):
    def setUp(self):
        self.plugin = _make_plugin()

    def test_ldaperror_returns_message_when_recent_error(self):
        """Returns formatted message string when error is within timeout (204-207)."""
        self.plugin._v_ldaperror_msg = "connection refused"
        self.plugin._v_ldaperror_timeout = time.time()   # very recent
        result = self.plugin.ldaperror
        self.assertIn("connection refused", result)
        self.assertIn("for", result)

    def test_ldaperror_returns_false_when_no_error_attribute(self):
        """Returns False when _v_ldaperror_msg is not set (line 208)."""
        result = self.plugin.ldaperror
        self.assertFalse(result)

    def test_ldaperror_returns_false_when_error_expired(self):
        """Returns False when error timeout has expired (line 208 branch)."""
        self.plugin._v_ldaperror_msg = "old error"
        self.plugin._v_ldaperror_timeout = time.time() - LDAP_ERROR_LOG_TIMEOUT - 1
        result = self.plugin.ldaperror
        self.assertFalse(result)


# ---------------------------------------------------------------------------
# reset  (line 214)
# ---------------------------------------------------------------------------

class TestReset(unittest.TestCase):
    def test_reset_executes_without_error(self):
        """reset() passes silently (line 214)."""
        plugin = _make_plugin()
        plugin.reset()   # should not raise


# ---------------------------------------------------------------------------
# authenticateCredentials  (lines 235, 239, 243, 245-248)
# ---------------------------------------------------------------------------

class TestAuthenticateCredentials(unittest.TestCase):
    def setUp(self):
        self.plugin = _make_plugin()
        self.plugin.is_plugin_active = MagicMock(return_value=True)

    def _call(self, credentials):
        return self.plugin.authenticateCredentials(credentials)

    def test_returns_none_when_plugin_not_active(self):
        """Returns None immediately when plugin is not active (line 235)."""
        self.plugin.is_plugin_active = MagicMock(return_value=False)
        with patch.object(type(self.plugin), "users", new_callable=PropertyMock):
            result = self._call({"login": "u", "password": "p"})
        self.assertIsNone(result)

    def test_returns_none_when_no_login(self):
        """Returns None when login is empty/missing (line 239)."""
        with patch.object(type(self.plugin), "users", new_callable=PropertyMock):
            self.assertIsNone(self._call({"login": "", "password": "p"}))

    def test_returns_none_when_no_password(self):
        """Returns None when password is empty/missing (line 239)."""
        with patch.object(type(self.plugin), "users", new_callable=PropertyMock):
            self.assertIsNone(self._call({"login": "u", "password": ""}))

    def test_returns_none_when_users_is_none(self):
        """Returns None when self.users is None (line 243)."""
        with patch.object(type(self.plugin), "users", new_callable=PropertyMock) as pu:
            pu.return_value = None
            result = self._call({"login": "u", "password": "p"})
        self.assertIsNone(result)

    def test_returns_userid_login_tuple_on_success(self):
        """Returns (userid, login) when authentication succeeds (lines 245-247)."""
        mock_users = MagicMock()
        mock_users.authenticate.return_value = "uid42"
        with patch.object(type(self.plugin), "users", new_callable=PropertyMock) as pu:
            pu.return_value = mock_users
            result = self._call({"login": "testuser", "password": "secret"})
        self.assertEqual(result, ("uid42", "testuser"))

    def test_returns_none_on_failed_authentication(self):
        """Returns None when authenticate() returns falsy (line 248)."""
        mock_users = MagicMock()
        mock_users.authenticate.return_value = None
        with patch.object(type(self.plugin), "users", new_callable=PropertyMock) as pu:
            pu.return_value = mock_users
            result = self._call({"login": "u", "password": "wrong"})
        self.assertIsNone(result)


# ---------------------------------------------------------------------------
# enumerateGroups  (lines 300, 303, 307, 313-320)
# ---------------------------------------------------------------------------

class TestEnumerateGroups(unittest.TestCase):
    def setUp(self):
        self.plugin = _make_plugin()
        self.plugin.is_plugin_active = MagicMock(return_value=True)
        self.plugin.getId = MagicMock(return_value="testplugin")

    def _call(self, **kw):
        return self.plugin.enumerateGroups(**kw)

    def test_returns_empty_when_not_active(self):
        """Returns () when plugin is not active for group enumeration (line 300)."""
        self.plugin.is_plugin_active = MagicMock(return_value=False)
        with patch.object(type(self.plugin), "groups", new_callable=PropertyMock):
            result = self._call()
        self.assertEqual(result, ())

    def test_returns_empty_when_no_groups(self):
        """Returns () when self.groups is None/falsy (line 303)."""
        with patch.object(type(self.plugin), "groups", new_callable=PropertyMock) as pg:
            pg.return_value = None
            result = self._call()
        self.assertEqual(result, ())

    def test_returns_all_groups_when_no_criteria(self):
        """Uses groups.ids to list all groups when no kw criteria (line 307)."""
        mock_groups = MagicMock()
        mock_groups.ids = ["grp1", "grp2"]
        with patch.object(type(self.plugin), "groups", new_callable=PropertyMock) as pg:
            pg.return_value = mock_groups
            result = self._call()
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["id"], "grp1")

    def test_returns_empty_on_value_error(self):
        """Returns () when groups.search raises ValueError (line 313)."""
        mock_groups = MagicMock()
        mock_groups.search.side_effect = ValueError("not unique")
        with patch.object(type(self.plugin), "groups", new_callable=PropertyMock) as pg:
            pg.return_value = mock_groups
            result = self._call(id="g1", exact_match=True)
        self.assertEqual(result, ())

    def test_sorts_by_id_when_sort_by_is_id(self):
        """Sorted results when sort_by='id' (line 315)."""
        mock_groups = MagicMock()
        mock_groups.ids = ["zzz", "aaa", "mmm"]
        with patch.object(type(self.plugin), "groups", new_callable=PropertyMock) as pg:
            pg.return_value = mock_groups
            result = self._call(sort_by="id")
        ids = [r["id"] for r in result]
        self.assertEqual(ids, sorted(ids))

    def test_limits_results_by_max_results(self):
        """Truncates results when len > max_results (lines 318-319)."""
        mock_groups = MagicMock()
        mock_groups.ids = ["g1", "g2", "g3", "g4"]
        with patch.object(type(self.plugin), "groups", new_callable=PropertyMock) as pg:
            pg.return_value = mock_groups
            result = self._call(max_results=2)
        self.assertEqual(len(result), 2)

    def test_returns_pluginid_in_each_item(self):
        """Each result dict has pluginid from self.getId() (lines 316-317)."""
        mock_groups = MagicMock()
        mock_groups.ids = ["grp1"]
        with patch.object(type(self.plugin), "groups", new_callable=PropertyMock) as pg:
            pg.return_value = mock_groups
            result = self._call()
        self.assertEqual(result[0]["pluginid"], "testplugin")


# ---------------------------------------------------------------------------
# getGroupsForPrincipal  (lines 337, 341-352)
# ---------------------------------------------------------------------------

class TestGetGroupsForPrincipal(unittest.TestCase):
    def setUp(self):
        self.plugin = _make_plugin()
        self.plugin.is_plugin_active = MagicMock(return_value=True)

    def _call(self, principal_id="u1"):
        principal = MagicMock()
        principal.getId.return_value = principal_id
        return self.plugin.getGroupsForPrincipal(principal)

    def test_returns_empty_tuple_when_not_active(self):
        """Returns () when plugin is not active for groups (line 337)."""
        self.plugin.is_plugin_active = MagicMock(return_value=False)
        with patch.object(type(self.plugin), "users", new_callable=PropertyMock):
            result = self._call()
        self.assertEqual(result, ())

    def test_returns_empty_tuple_when_no_users(self):
        """Returns () when self.users is None (line ~340)."""
        with patch.object(type(self.plugin), "users", new_callable=PropertyMock) as pu:
            pu.return_value = None
            result = self._call()
        self.assertEqual(result, ())

    def test_returns_empty_tuple_on_key_error(self):
        """Returns () when users[id] raises KeyError (lines 341-347)."""
        mock_users = MagicMock()
        mock_users.__getitem__.side_effect = KeyError("u1")
        with patch.object(type(self.plugin), "users", new_callable=PropertyMock) as pu:
            pu.return_value = mock_users
            result = self._call("u1")
        self.assertEqual(result, ())

    def test_returns_empty_tuple_on_exception_getting_group_ids(self):
        """Returns () when ugm_principal.group_ids raises Exception (lines 348-352)."""
        mock_users = MagicMock()
        ugm_principal = MagicMock()
        type(ugm_principal).group_ids = PropertyMock(side_effect=Exception("error"))
        mock_users.__getitem__.return_value = ugm_principal
        with patch.object(type(self.plugin), "users", new_callable=PropertyMock) as pu:
            pu.return_value = mock_users
            with patch("pas.plugins.ldap.plugin.logger"):
                result = self._call("u1")
        self.assertEqual(result, ())

    def test_returns_group_ids_on_success(self):
        """Returns group_ids when everything succeeds."""
        mock_users = MagicMock()
        ugm_principal = MagicMock()
        ugm_principal.group_ids = ["group1", "group2"]
        mock_users.__getitem__.return_value = ugm_principal
        with patch.object(type(self.plugin), "users", new_callable=PropertyMock) as pu:
            pu.return_value = mock_users
            result = self._call("u1")
        self.assertEqual(result, ["group1", "group2"])


# ---------------------------------------------------------------------------
# enumerateUsers  (lines 412, 417, 421, 425, 429, 441-448)
# ---------------------------------------------------------------------------

class TestEnumerateUsers(unittest.TestCase):
    def setUp(self):
        self.plugin = _make_plugin()
        self.plugin.is_plugin_active = MagicMock(return_value=True)
        self.plugin.getId = MagicMock(return_value="testplugin")

    def _call(self, **kw):
        return self.plugin.enumerateUsers(**kw)

    def test_returns_empty_when_not_active(self):
        """Returns () when plugin is not active (line 412)."""
        self.plugin.is_plugin_active = MagicMock(return_value=False)
        with patch.object(type(self.plugin), "users", new_callable=PropertyMock):
            result = self._call()
        self.assertEqual(result, ())

    def test_returns_empty_when_login_is_not_str(self):
        """Returns () when login is a non-string sequence (line 417 executed, caught by error handler)."""
        with patch.object(type(self.plugin), "users", new_callable=PropertyMock):
            with patch("pas.plugins.ldap.plugin.logger"):
                result = self._call(login=["user1", "user2"])
        self.assertEqual(result, ())

    def test_removes_name_when_login_and_name_both_in_kw(self):
        """Deletes 'name' from criteria when both 'login' and 'name' given (line 421)."""
        mock_users = MagicMock()
        mock_users.search.return_value = []
        with patch.object(type(self.plugin), "users", new_callable=PropertyMock) as pu:
            pu.return_value = mock_users
            self._call(login="bob", name="bob")
        # 'name' should have been deleted; search called without 'name'
        call_kw = mock_users.search.call_args[1]
        self.assertNotIn("name", call_kw.get("criteria", {}))

    def test_returns_empty_when_id_is_not_str(self):
        """Returns () when id is a non-string sequence (line 425 executed, caught by error handler)."""
        with patch.object(type(self.plugin), "users", new_callable=PropertyMock):
            with patch("pas.plugins.ldap.plugin.logger"):
                result = self._call(id=["u1", "u2"])
        self.assertEqual(result, ())

    def test_returns_empty_when_no_users(self):
        """Returns () when self.users is None (line 429)."""
        with patch.object(type(self.plugin), "users", new_callable=PropertyMock) as pu:
            pu.return_value = None
            result = self._call(id="u1")
        self.assertEqual(result, ())

    def test_returns_empty_on_value_error(self):
        """Returns () when users.search raises ValueError (line 441)."""
        mock_users = MagicMock()
        mock_users.search.side_effect = ValueError("not unique")
        with patch.object(type(self.plugin), "users", new_callable=PropertyMock) as pu:
            pu.return_value = mock_users
            result = self._call(id="u1", exact_match=True)
        self.assertEqual(result, ())

    def test_builds_result_list_from_search(self):
        """Builds list of dicts with id/login/pluginid (lines 442-445)."""
        mock_users = MagicMock()
        mock_users.search.return_value = [
            ("uid0", {"login": ["cn0"]}),
            ("uid1", {"login": ["cn1"]}),
        ]
        with patch.object(type(self.plugin), "users", new_callable=PropertyMock) as pu:
            pu.return_value = mock_users
            result = self._call(id="uid*")
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["id"], "uid0")
        self.assertEqual(result[0]["login"], "cn0")
        self.assertEqual(result[0]["pluginid"], "testplugin")

    def test_limits_results_by_max_results(self):
        """Truncates results when len > max_results (lines 446-447)."""
        mock_users = MagicMock()
        mock_users.search.return_value = [
            ("uid0", {"login": ["cn0"]}),
            ("uid1", {"login": ["cn1"]}),
            ("uid2", {"login": ["cn2"]}),
        ]
        with patch.object(type(self.plugin), "users", new_callable=PropertyMock) as pu:
            pu.return_value = mock_users
            result = self._call(id="uid*", max_results=2)
        self.assertEqual(len(result), 2)


# ---------------------------------------------------------------------------
# getRolesForPrincipal  (lines 466, 468)
# ---------------------------------------------------------------------------

class TestGetRolesForPrincipal(unittest.TestCase):
    def setUp(self):
        self.plugin = _make_plugin()

    def test_returns_empty_when_no_users(self):
        """Returns () when self.users is None (line 466)."""
        with patch.object(type(self.plugin), "users", new_callable=PropertyMock) as pu:
            pu.return_value = None
            principal = MagicMock()
            result = self.plugin.getRolesForPrincipal(principal)
        self.assertEqual(result, ())

    def test_returns_roles_when_user_exists(self):
        """Returns roles tuple when user is found via enumerateUsers (line 468)."""
        mock_users = MagicMock()
        principal = MagicMock()
        principal.getId.return_value = "uid0"
        self.plugin.is_plugin_active = MagicMock(return_value=True)
        self.plugin.getId = MagicMock(return_value="testplugin")

        mock_users.search.return_value = [("uid0", {"login": ["cn0"]})]
        mock_ldap_props = MagicMock()
        mock_ldap_props.roles = ["Member", "Reviewer"]

        with patch.object(type(self.plugin), "users", new_callable=PropertyMock) as pu:
            pu.return_value = mock_users
            with patch.object(
                type(self.plugin), "_ldap_props", new_callable=PropertyMock
            ) as pp:
                pp.return_value = mock_ldap_props
                result = self.plugin.getRolesForPrincipal(principal)
        self.assertIn("Member", result)
        self.assertIn("Reviewer", result)


# ---------------------------------------------------------------------------
# updateUser / updateEveryLoginName  (lines 485, 501)
# ---------------------------------------------------------------------------

class TestUpdateMethods(unittest.TestCase):
    def setUp(self):
        self.plugin = _make_plugin()

    def test_update_user_returns_false(self):
        """updateUser always returns False (line 485)."""
        result = self.plugin.updateUser("uid0", "new_login")
        self.assertFalse(result)

    def test_update_every_login_name_returns_none(self):
        """updateEveryLoginName returns None (line 501)."""
        result = self.plugin.updateEveryLoginName()
        self.assertIsNone(result)


# ---------------------------------------------------------------------------
# getPropertiesForUser  (lines 584, 586-595)
# setPropertiesForUser  (line 606)
# deleteUser            (line 615)
# ---------------------------------------------------------------------------

class TestPropertiesMethods(unittest.TestCase):
    def setUp(self):
        self.plugin = _make_plugin()
        self.plugin.is_plugin_active = MagicMock(return_value=True)
        self.plugin.getId = MagicMock(return_value="testplugin")

    def test_getPropertiesForUser_returns_empty_when_not_active(self):
        """Returns {} when plugin is not active (line 584)."""
        self.plugin.is_plugin_active = MagicMock(return_value=False)
        user = MagicMock()
        result = self.plugin.getPropertiesForUser(user)
        self.assertEqual(result, {})

    def test_getPropertiesForUser_decodes_bytes_ugid(self):
        """Decodes bytes user id to str (line 587)."""
        user = MagicMock()
        user.getId.return_value = b"uid0"
        self.plugin.enumerateUsers = MagicMock(return_value=[])
        self.plugin.enumerateGroups = MagicMock(return_value=[])
        result = self.plugin.getPropertiesForUser(user)
        self.assertEqual(result, {})

    def test_getPropertiesForUser_returns_sheet_when_user_found(self):
        """Returns LDAPUserPropertySheet when user is enumerated (line 592)."""
        user = MagicMock()
        user.getId.return_value = "uid0"
        self.plugin.enumerateUsers = MagicMock(
            return_value=[{"id": "uid0", "login": "cn0", "pluginid": "testplugin"}]
        )
        self.plugin.enumerateGroups = MagicMock(return_value=[])
        with patch("pas.plugins.ldap.plugin.LDAPUserPropertySheet") as MockSheet:
            result = self.plugin.getPropertiesForUser(user)
        MockSheet.assert_called_once_with(user, self.plugin)
        self.assertEqual(result, MockSheet.return_value)

    def test_getPropertiesForUser_returns_empty_on_key_error(self):
        """Returns {} when enumerateUsers raises KeyError (lines 593-595)."""
        user = MagicMock()
        user.getId.return_value = "uid0"
        self.plugin.enumerateUsers = MagicMock(side_effect=KeyError("missing"))
        result = self.plugin.getPropertiesForUser(user)
        self.assertEqual(result, {})

    def test_getPropertiesForUser_returns_empty_when_not_found(self):
        """Returns {} when user/group not found via enumeration (line 595)."""
        user = MagicMock()
        user.getId.return_value = "uid_unknown"
        self.plugin.enumerateUsers = MagicMock(return_value=[])
        self.plugin.enumerateGroups = MagicMock(return_value=[])
        result = self.plugin.getPropertiesForUser(user)
        self.assertEqual(result, {})

    def test_setPropertiesForUser_does_nothing(self):
        """setPropertiesForUser is a no-op (line 606)."""
        user = MagicMock()
        sheet = MagicMock()
        result = self.plugin.setPropertiesForUser(user, sheet)
        self.assertIsNone(result)

    def test_deleteUser_does_nothing(self):
        """deleteUser is a no-op (line 615)."""
        result = self.plugin.deleteUser("uid0")
        self.assertIsNone(result)


# ---------------------------------------------------------------------------
# doAddUser / doChangeUser / doDeleteUser  (lines 629, 641-643, 654)
# ---------------------------------------------------------------------------

class TestUserManagementMethods(unittest.TestCase):
    def setUp(self):
        self.plugin = _make_plugin()

    def test_doAddUser_returns_false(self):
        """doAddUser always returns False (line 629)."""
        result = self.plugin.doAddUser("login", "password")
        self.assertFalse(result)

    def test_doChangeUser_raises_runtime_error_when_user_not_found(self):
        """doChangeUser raises RuntimeError when passwd raises KeyError (641-643)."""
        mock_users = MagicMock()
        mock_users.passwd.side_effect = KeyError("uid_unknown")
        with patch.object(type(self.plugin), "users", new_callable=PropertyMock) as pu:
            pu.return_value = mock_users
            with patch("pas.plugins.ldap.plugin.logger"):
                with self.assertRaises(RuntimeError) as ctx:
                    self.plugin.doChangeUser("uid_unknown", "newpass")
        self.assertIn("uid_unknown", str(ctx.exception))

    def test_doDeleteUser_returns_false(self):
        """doDeleteUser always returns False (line 654)."""
        result = self.plugin.doDeleteUser("login")
        self.assertFalse(result)


# ---------------------------------------------------------------------------
# getGroupById  (lines 700, 702, 704, 707-729)
# ---------------------------------------------------------------------------

class TestGetGroupById(unittest.TestCase):
    def setUp(self):
        self.plugin = _make_plugin()
        self.plugin.is_plugin_active = MagicMock(return_value=True)

    def test_returns_none_when_not_active(self):
        """Returns None when plugin is not active (line 700)."""
        self.plugin.is_plugin_active = MagicMock(return_value=False)
        with patch.object(type(self.plugin), "groups", new_callable=PropertyMock):
            result = self.plugin.getGroupById("grp1")
        self.assertIsNone(result)

    def test_returns_none_when_group_id_is_none(self):
        """Returns None when group_id is None (line 702)."""
        with patch.object(type(self.plugin), "groups", new_callable=PropertyMock):
            result = self.plugin.getGroupById(None)
        self.assertIsNone(result)

    def test_decodes_bytes_group_id(self):
        """Decodes bytes group_id to str (line 704); returns None when not in keys."""
        with patch.object(type(self.plugin), "groups", new_callable=PropertyMock) as pg:
            mock_groups = MagicMock()
            # After decoding b"grp1" → "grp1", group is NOT in keys → returns default
            mock_groups.keys.return_value = []
            pg.return_value = mock_groups
            result = self.plugin.getGroupById(b"grp1")
        self.assertIsNone(result)

    def test_returns_none_when_group_not_found(self):
        """Returns None when group_id not in groups.keys() (line 706 guard)."""
        with patch.object(type(self.plugin), "groups", new_callable=PropertyMock) as pg:
            mock_groups = MagicMock()
            mock_groups.keys.return_value = ["other"]
            pg.return_value = mock_groups
            result = self.plugin.getGroupById("grp_missing")
        self.assertIsNone(result)

    def test_returns_plone_group_when_found(self):
        """Builds and returns a PloneGroup when group exists (lines 707-729)."""
        # Set up mock groups
        mock_ugmgroup = MagicMock()
        mock_ugmgroup.id = "grp1"
        mock_ugmgroup.attrs.get.return_value = "Group One"

        mock_groups = MagicMock()
        mock_groups.keys.return_value = ["grp1"]
        mock_groups.__getitem__.return_value = mock_ugmgroup

        # Set up mock PAS
        mock_pas = MagicMock()
        mock_plugins = MagicMock()
        mock_plugins.listPlugins.return_value = []  # no property/role finders
        mock_pas.plugins = mock_plugins
        mock_pas._getGroupsForPrincipal.return_value = []

        self.plugin._getPAS = MagicMock(return_value=mock_pas)

        with patch.object(type(self.plugin), "groups", new_callable=PropertyMock) as pg:
            pg.return_value = mock_groups
            with patch("pas.plugins.ldap.plugin.PloneGroup") as MockPloneGroup:
                mock_group = MagicMock()
                MockPloneGroup.return_value.__of__ = MagicMock(return_value=mock_group)
                result = self.plugin.getGroupById("grp1")
        # Should have tried to create a PloneGroup
        MockPloneGroup.assert_called_once_with("grp1", "Group One")

    def test_adds_properties_to_group(self):
        """Iterates property finders and adds non-empty property sheets (line 720)."""
        mock_ugmgroup = MagicMock()
        mock_ugmgroup.id = "grp1"
        mock_ugmgroup.attrs.get.return_value = None

        mock_groups = MagicMock()
        mock_groups.keys.return_value = ["grp1"]
        mock_groups.__getitem__.return_value = mock_ugmgroup

        mock_propfinder = MagicMock()
        mock_propdata = MagicMock()
        mock_propfinder.getPropertiesForUser.return_value = mock_propdata

        mock_pas = MagicMock()
        mock_plugins = MagicMock()
        # Return one propfinder and no role finder
        mock_plugins.listPlugins.side_effect = [
            [("propfinder1", mock_propfinder)],  # IPropertiesPlugin
            [],                                   # IRolesPlugin
        ]
        mock_pas.plugins = mock_plugins
        mock_pas._getGroupsForPrincipal.return_value = []
        self.plugin._getPAS = MagicMock(return_value=mock_pas)

        with patch.object(type(self.plugin), "groups", new_callable=PropertyMock) as pg:
            pg.return_value = mock_groups
            with patch("pas.plugins.ldap.plugin.PloneGroup") as MockPloneGroup:
                mock_group = MagicMock()
                MockPloneGroup.return_value.__of__ = MagicMock(return_value=mock_group)
                self.plugin.getGroupById("grp1")
        mock_group.addPropertysheet.assert_called_once_with("propfinder1", mock_propdata)

    def test_adds_roles_to_group(self):
        """Iterates role makers and adds non-empty roles (line 728)."""
        mock_ugmgroup = MagicMock()
        mock_ugmgroup.id = "grp1"
        mock_ugmgroup.attrs.get.return_value = None

        mock_groups = MagicMock()
        mock_groups.keys.return_value = ["grp1"]
        mock_groups.__getitem__.return_value = mock_ugmgroup

        mock_rolemaker = MagicMock()
        mock_rolemaker.getRolesForPrincipal.return_value = ["Member"]

        mock_pas = MagicMock()
        mock_plugins = MagicMock()
        mock_plugins.listPlugins.side_effect = [
            [],                                     # IPropertiesPlugin
            [("rolemaker1", mock_rolemaker)],        # IRolesPlugin
        ]
        mock_pas.plugins = mock_plugins
        mock_pas._getGroupsForPrincipal.return_value = []
        self.plugin._getPAS = MagicMock(return_value=mock_pas)

        with patch.object(type(self.plugin), "groups", new_callable=PropertyMock) as pg:
            pg.return_value = mock_groups
            with patch("pas.plugins.ldap.plugin.PloneGroup") as MockPloneGroup:
                mock_group = MagicMock()
                MockPloneGroup.return_value.__of__ = MagicMock(return_value=mock_group)
                self.plugin.getGroupById("grp1")
        mock_group._addRoles.assert_called_once_with(["Member"])


# ---------------------------------------------------------------------------
# getGroupIds  (line 748)
# ---------------------------------------------------------------------------

class TestGetGroupIds(unittest.TestCase):
    def setUp(self):
        self.plugin = _make_plugin()
        self.plugin.is_plugin_active = MagicMock(return_value=True)

    def test_returns_empty_when_not_active(self):
        """Returns [] when plugin is not active (line 748)."""
        self.plugin.is_plugin_active = MagicMock(return_value=False)
        with patch.object(type(self.plugin), "groups", new_callable=PropertyMock):
            result = self.plugin.getGroupIds()
        self.assertEqual(result, [])

    def test_returns_group_ids_when_active(self):
        """Returns groups.ids when plugin is active."""
        mock_groups = MagicMock()
        mock_groups.ids = ["g1", "g2"]
        with patch.object(type(self.plugin), "groups", new_callable=PropertyMock) as pg:
            pg.return_value = mock_groups
            result = self.plugin.getGroupIds()
        self.assertEqual(result, ["g1", "g2"])


# ---------------------------------------------------------------------------
# getGroupMembers  (lines 758, 762-763)
# ---------------------------------------------------------------------------

class TestGetGroupMembers(unittest.TestCase):
    def setUp(self):
        self.plugin = _make_plugin()
        self.plugin.is_plugin_active = MagicMock(return_value=True)

    def test_returns_empty_when_not_active(self):
        """Returns () when plugin is not active (line 758)."""
        self.plugin.is_plugin_active = MagicMock(return_value=False)
        with patch.object(type(self.plugin), "groups", new_callable=PropertyMock):
            result = self.plugin.getGroupMembers("grp1")
        self.assertEqual(result, ())

    def test_returns_empty_on_key_error(self):
        """Returns () when groups[group_id] raises KeyError (lines 762-763)."""
        mock_groups = MagicMock()
        mock_groups.__getitem__.side_effect = KeyError("grp_missing")
        with patch.object(type(self.plugin), "groups", new_callable=PropertyMock) as pg:
            pg.return_value = mock_groups
            result = self.plugin.getGroupMembers("grp_missing")
        self.assertEqual(result, ())

    def test_returns_member_ids_tuple(self):
        """Returns tuple of member_ids when group found."""
        mock_group = MagicMock()
        mock_group.member_ids = ["u1", "u2"]
        mock_groups = MagicMock()
        mock_groups.__getitem__.return_value = mock_group
        with patch.object(type(self.plugin), "groups", new_callable=PropertyMock) as pg:
            pg.return_value = mock_groups
            result = self.plugin.getGroupMembers("grp1")
        self.assertEqual(result, ("u1", "u2"))


# ---------------------------------------------------------------------------
# allowPasswordSet  (lines 774, 777, 779)
# ---------------------------------------------------------------------------

class TestAllowPasswordSet(unittest.TestCase):
    def setUp(self):
        self.plugin = _make_plugin()

    def test_returns_false_when_no_users(self):
        """Returns False when self.users is None (line 774)."""
        with patch.object(type(self.plugin), "users", new_callable=PropertyMock) as pu:
            pu.return_value = None
            result = self.plugin.allowPasswordSet("uid0")
        self.assertFalse(result)

    def test_returns_true_when_user_found(self):
        """Returns True when search finds at least one result (line 777)."""
        mock_users = MagicMock()
        mock_users.search.return_value = [("uid0", {})]
        with patch.object(type(self.plugin), "users", new_callable=PropertyMock) as pu:
            pu.return_value = mock_users
            result = self.plugin.allowPasswordSet("uid0")
        self.assertTrue(result)

    def test_returns_false_when_user_not_found(self):
        """Returns False when search finds no results (line 777 len==0)."""
        mock_users = MagicMock()
        mock_users.search.return_value = []
        with patch.object(type(self.plugin), "users", new_callable=PropertyMock) as pu:
            pu.return_value = mock_users
            result = self.plugin.allowPasswordSet("uid_unknown")
        self.assertFalse(result)

    def test_returns_false_on_value_error(self):
        """Returns False when users.search raises ValueError (line 779)."""
        mock_users = MagicMock()
        mock_users.search.side_effect = ValueError("not unique")
        with patch.object(type(self.plugin), "users", new_callable=PropertyMock) as pu:
            pu.return_value = mock_users
            result = self.plugin.allowPasswordSet("uid0")
        self.assertFalse(result)


# ---------------------------------------------------------------------------
# is_plugin_active real body  (lines 153-155)
# ---------------------------------------------------------------------------

class TestIsPluginActiveRealBody(unittest.TestCase):
    def test_returns_true_when_plugin_id_in_list(self):
        """Real method: returns True when getId() is in listPluginIds (153-155)."""
        plugin = _make_plugin()
        plugin.getId = MagicMock(return_value="testplugin")
        mock_pas = MagicMock()
        mock_pas.plugins.listPluginIds.return_value = ["testplugin", "other"]
        plugin._getPAS = MagicMock(return_value=mock_pas)
        result = plugin.is_plugin_active(MagicMock())
        self.assertTrue(result)

    def test_returns_false_when_plugin_id_not_in_list(self):
        """Real method: returns False when getId() is NOT in listPluginIds (155)."""
        plugin = _make_plugin()
        plugin.getId = MagicMock(return_value="testplugin")
        mock_pas = MagicMock()
        mock_pas.plugins.listPluginIds.return_value = ["other_plugin"]
        plugin._getPAS = MagicMock(return_value=mock_pas)
        result = plugin.is_plugin_active(MagicMock())
        self.assertFalse(result)


# ---------------------------------------------------------------------------
# _ldap_props property  (line 172)
# ---------------------------------------------------------------------------

class TestLdapPropsProperty(unittest.TestCase):
    def test_returns_ildapprops_adapter(self):
        """_ldap_props calls ILDAPProps(self) and returns the result (line 172)."""
        plugin = _make_plugin()
        with patch("pas.plugins.ldap.plugin.ILDAPProps") as MockProps:
            result = plugin._ldap_props
        MockProps.assert_called_once_with(plugin)
        self.assertEqual(result, MockProps.return_value)


# ---------------------------------------------------------------------------
# _ugm() method  (lines 176-184)
# ---------------------------------------------------------------------------

class TestUgmMethod(unittest.TestCase):
    def test_ugm_builds_and_caches_ugm_on_cache_miss(self):
        """Cache miss: builds Ugm, stores in cache, returns it (lines 176-184)."""
        plugin = _make_plugin()
        mock_cache = MagicMock()
        mock_cache.get.return_value = VALUE_NOT_CACHED  # cache miss sentinel
        mock_ugm = MagicMock()

        with patch("pas.plugins.ldap.plugin.get_plugin_cache", return_value=mock_cache):
            with patch("pas.plugins.ldap.plugin.ILDAPUsersConfig"):
                with patch("pas.plugins.ldap.plugin.ILDAPGroupsConfig"):
                    with patch("pas.plugins.ldap.plugin.Ugm", return_value=mock_ugm):
                        with patch("pas.plugins.ldap.plugin.ILDAPProps"):
                            result = plugin._ugm()

        self.assertEqual(result, mock_ugm)
        mock_cache.set.assert_called_once_with(mock_ugm)

    def test_ugm_returns_cached_value_on_cache_hit(self):
        """Cache hit: returns cached ugm immediately without rebuilding (line 179)."""
        plugin = _make_plugin()
        cached_ugm = MagicMock()
        mock_cache = MagicMock()
        mock_cache.get.return_value = cached_ugm  # something other than VALUE_NOT_CACHED

        with patch("pas.plugins.ldap.plugin.get_plugin_cache", return_value=mock_cache):
            result = plugin._ugm()

        self.assertEqual(result, cached_ugm)
        mock_cache.set.assert_not_called()


# ---------------------------------------------------------------------------
# groups / users real property bodies  (lines 191, 198)
# ---------------------------------------------------------------------------

class TestGroupsUsersPropertyBodies(unittest.TestCase):
    def test_groups_property_calls_ugm_groups(self):
        """Real groups property body returns self._ugm().groups (line 191)."""
        plugin = _make_plugin()
        mock_ugm = MagicMock()
        mock_ugm.groups = MagicMock(name="ugm_groups")
        plugin._ugm = MagicMock(return_value=mock_ugm)
        result = plugin.groups
        self.assertEqual(result, mock_ugm.groups)

    def test_users_property_calls_ugm_users(self):
        """Real users property body returns self._ugm().users (line 198)."""
        plugin = _make_plugin()
        mock_ugm = MagicMock()
        mock_ugm.users = MagicMock(name="ugm_users")
        plugin._ugm = MagicMock(return_value=mock_ugm)
        result = plugin.users
        self.assertEqual(result, mock_ugm.users)


# ---------------------------------------------------------------------------
# getRolesForPrincipal "user not found" branch  (line 469)
# ---------------------------------------------------------------------------

class TestGetRolesForPrincipalNotFound(unittest.TestCase):
    def test_returns_empty_when_enumerateusers_finds_nothing(self):
        """Returns () when users is truthy but enumerateUsers returns () (line 469)."""
        plugin = _make_plugin()
        mock_users = MagicMock()
        mock_users.search.return_value = []  # enumerateUsers will return ()
        principal = MagicMock()
        principal.getId.return_value = "uid_ghost"

        with patch.object(type(plugin), "users", new_callable=PropertyMock) as pu:
            pu.return_value = mock_users
            result = plugin.getRolesForPrincipal(principal)
        self.assertEqual(result, ())


# ---------------------------------------------------------------------------
# Group management stubs  (lines 513, 522, 531, 542, 551, 560)
# ---------------------------------------------------------------------------

class TestGroupManagementStubs(unittest.TestCase):
    def setUp(self):
        self.plugin = _make_plugin()

    def test_addGroup_returns_false(self):
        """addGroup always returns False (line 513)."""
        self.assertFalse(self.plugin.addGroup("grp1"))

    def test_addPrincipalToGroup_returns_false(self):
        """addPrincipalToGroup always returns False (line 522)."""
        self.assertFalse(self.plugin.addPrincipalToGroup("u1", "grp1"))

    def test_updateGroup_returns_false(self):
        """updateGroup always returns False (line 531)."""
        self.assertFalse(self.plugin.updateGroup("grp1"))

    def test_setRolesForGroup_returns_false(self):
        """setRolesForGroup always returns False (line 542)."""
        self.assertFalse(self.plugin.setRolesForGroup("grp1", ["Member"]))

    def test_removeGroup_returns_false(self):
        """removeGroup always returns False (line 551)."""
        self.assertFalse(self.plugin.removeGroup("grp1"))

    def test_removePrincipalFromGroup_returns_false(self):
        """removePrincipalFromGroup always returns False (line 560)."""
        self.assertFalse(self.plugin.removePrincipalFromGroup("u1", "grp1"))


# ---------------------------------------------------------------------------
# Capability allow methods  (lines 664, 677, 686)
# ---------------------------------------------------------------------------

class TestCapabilityAllowMethods(unittest.TestCase):
    def setUp(self):
        self.plugin = _make_plugin()

    def test_allowDeletePrincipal_returns_false(self):
        """allowDeletePrincipal always returns False (line 664)."""
        self.assertFalse(self.plugin.allowDeletePrincipal("u1"))

    def test_allowGroupAdd_returns_false(self):
        """allowGroupAdd always returns False (line 677)."""
        self.assertFalse(self.plugin.allowGroupAdd("u1", "grp1"))

    def test_allowGroupRemove_returns_false(self):
        """allowGroupRemove always returns False (line 686)."""
        self.assertFalse(self.plugin.allowGroupRemove("u1", "grp1"))


# ---------------------------------------------------------------------------
# getGroupById continue branches  (lines 719, 727)
# ---------------------------------------------------------------------------

class TestGetGroupByIdContinueBranches(unittest.TestCase):
    def setUp(self):
        self.plugin = _make_plugin()
        self.plugin.is_plugin_active = MagicMock(return_value=True)

    def _make_groups_mock(self, group_id="grp1"):
        mock_ugmgroup = MagicMock()
        mock_ugmgroup.id = group_id
        mock_ugmgroup.attrs.get.return_value = "A Group"
        mock_groups = MagicMock()
        mock_groups.keys.return_value = [group_id]
        mock_groups.__getitem__.return_value = mock_ugmgroup
        return mock_groups

    def test_skips_propfinder_with_empty_data(self):
        """Propfinder returning falsy data hits 'continue' at line 719."""
        mock_groups = self._make_groups_mock()
        mock_propfinder = MagicMock()
        mock_propfinder.getPropertiesForUser.return_value = {}  # falsy

        mock_pas = MagicMock()
        mock_plugins = MagicMock()
        mock_plugins.listPlugins.side_effect = [
            [("propfinder1", mock_propfinder)],  # IPropertiesPlugin
            [],                                   # IRolesPlugin
        ]
        mock_pas.plugins = mock_plugins
        mock_pas._getGroupsForPrincipal.return_value = []
        self.plugin._getPAS = MagicMock(return_value=mock_pas)

        with patch.object(type(self.plugin), "groups", new_callable=PropertyMock) as pg:
            pg.return_value = mock_groups
            with patch("pas.plugins.ldap.plugin.PloneGroup") as MockPloneGroup:
                mock_group = MagicMock()
                MockPloneGroup.return_value.__of__ = MagicMock(return_value=mock_group)
                self.plugin.getGroupById("grp1")
        # addPropertysheet should NOT have been called because data was falsy
        mock_group.addPropertysheet.assert_not_called()

    def test_skips_rolemaker_with_empty_roles(self):
        """Rolemaker returning falsy roles hits 'continue' at line 727."""
        mock_groups = self._make_groups_mock()
        mock_rolemaker = MagicMock()
        mock_rolemaker.getRolesForPrincipal.return_value = ()  # falsy

        mock_pas = MagicMock()
        mock_plugins = MagicMock()
        mock_plugins.listPlugins.side_effect = [
            [],                                    # IPropertiesPlugin
            [("rolemaker1", mock_rolemaker)],       # IRolesPlugin
        ]
        mock_pas.plugins = mock_plugins
        mock_pas._getGroupsForPrincipal.return_value = []
        self.plugin._getPAS = MagicMock(return_value=mock_pas)

        with patch.object(type(self.plugin), "groups", new_callable=PropertyMock) as pg:
            pg.return_value = mock_groups
            with patch("pas.plugins.ldap.plugin.PloneGroup") as MockPloneGroup:
                mock_group = MagicMock()
                MockPloneGroup.return_value.__of__ = MagicMock(return_value=mock_group)
                self.plugin.getGroupById("grp1")
        # _addRoles should NOT have been called because roles was falsy
        mock_group._addRoles.assert_not_called()


# ---------------------------------------------------------------------------
# getGroups  (line 739)
# ---------------------------------------------------------------------------

class TestGetGroups(unittest.TestCase):
    def test_getGroups_returns_list_via_getGroupById(self):
        """getGroups maps getGroupById over getGroupIds (line 739)."""
        plugin = _make_plugin()
        plugin.getGroupIds = MagicMock(return_value=["g1", "g2"])
        mock_g1 = MagicMock(name="group_g1")
        mock_g2 = MagicMock(name="group_g2")
        plugin.getGroupById = MagicMock(side_effect=[mock_g1, mock_g2])
        result = plugin.getGroups()
        self.assertEqual(result, [mock_g1, mock_g2])
        plugin.getGroupById.assert_any_call("g1")
        plugin.getGroupById.assert_any_call("g2")

    def test_getGroups_returns_empty_list_when_no_groups(self):
        """getGroups returns [] when getGroupIds returns empty list."""
        plugin = _make_plugin()
        plugin.getGroupIds = MagicMock(return_value=[])
        plugin.getGroupById = MagicMock()
        result = plugin.getGroups()
        self.assertEqual(result, [])
        plugin.getGroupById.assert_not_called()
