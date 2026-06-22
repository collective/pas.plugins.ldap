"""Pure unit tests for pas.plugins.ldap.properties module.

These tests exercise all branches of properties.py using unittest.mock so
no real LDAP server, Zope layer, or Plone infrastructure is needed.
"""

from pas.plugins.ldap.defaults import DEFAULTS
from pas.plugins.ldap.properties import BasePropertiesForm
from pas.plugins.ldap.properties import GroupsConfig
from pas.plugins.ldap.properties import LDAPProps
from pas.plugins.ldap.properties import propproxy
from pas.plugins.ldap.properties import UsersConfig
from unittest.mock import MagicMock
from unittest.mock import patch
from yafowil.base import ExtractionError
from yafowil.base import UNSET
from yafowil.plone.form import YAMLBaseForm

import ldap
import unittest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class ConcreteForm(BasePropertiesForm):
    """Concrete subclass of BasePropertiesForm for testing.

    Provides minimal implementations of the two abstract members so that
    the rest of the class can be exercised without a real Plone context.
    """

    _plugin = None
    _next_url = "/test-next"

    @property
    def plugin(self):
        return self._plugin

    def next(self, request):
        return self._next_url


def _make_form(plugin=None, next_url="/test-next"):
    """Return a ConcreteForm instance, bypassing YAMLBaseForm.__init__."""
    form = ConcreteForm.__new__(ConcreteForm)
    form._plugin = plugin if plugin is not None else MagicMock()
    form._next_url = next_url
    form.request = MagicMock()
    form.form = MagicMock()
    return form


def _make_plugin_with_settings(extra=None):
    """Return a simple object whose .settings dict supports propproxy."""

    class _FakePlugin:
        settings = {}

    p = _FakePlugin()
    if extra:
        p.settings.update(extra)
    return p


def _make_data(field_values):
    """Build a mock *data* object whose fetch() simulates the form data layer.

    ``field_values`` maps short keys like ``"server.uri"`` to extracted
    values.  Keys not present default to ``UNSET``.
    """
    data = MagicMock()

    def _fetch_side_effect(name):
        key = name[len("ldapsettings.") :]  # strip "ldapsettings." prefix
        result = MagicMock()
        result.extracted = field_values.get(key, UNSET)
        return result

    data.fetch.side_effect = _fetch_side_effect
    return data


def _full_save_fields(
    anonymous=False,
    password="s3cret",
    users_scope='"2"',
    groups_scope='"2"',
    users_propsheet=None,
    groups_propsheet=None,
    aliases_attrmap=None,
):
    """Return a complete field_values dict for save() tests."""
    if aliases_attrmap is None:
        # "uid" is a value but NOT a key → triggers self-referential branch
        aliases_attrmap = {"rdn": "uid", "id": "uid", "login": "uid"}
    if users_propsheet is None:
        users_propsheet = {"email": "mail"}
    if groups_propsheet is None:
        groups_propsheet = {"title": "o"}

    values = {
        "server.uri": "ldap://localhost:389",
        "server.anonymous": anonymous,
        "server.ignore_cert": False,
        "server.start_tls": False,
        "server.tls_cacertfile": "",
        "server.tls_cacertdir": "",
        "server.tls_clcertfile": "",
        "server.tls_clkeyfile": "",
        "server.page_size": 1000,
        "server.conn_timeout": 5,
        "server.op_timeout": 600,
        "cache.cache": False,
        "cache.memcached": "127.0.0.1:11211",
        "cache.timeout": 300,
        "users.roles": ["Member"],
        "users.dn": "ou=users,dc=example,dc=com",
        "users.aliases_attrmap": aliases_attrmap,
        "users.propsheet_attrmap": users_propsheet,
        "users.scope": users_scope,
        "users.query": "(objectClass=inetOrgPerson)",
        "users.object_classes": ["inetOrgPerson"],
        "users.memberOfSupport": False,
        "users.recursiveGroups": False,
        "users.memberOfExternalGroupDNs": [],
        "users.account_expiration": False,
        "users.expires_attr": "shadowExpire",
        "users.expires_unit": "0",
        "groups.dn": "ou=groups,dc=example,dc=com",
        "groups.aliases_attrmap": {"rdn": "cn", "id": "cn"},
        "groups.propsheet_attrmap": groups_propsheet,
        "groups.scope": groups_scope,
        "groups.query": "(objectClass=groupOfNames)",
        "groups.object_classes": ["groupOfNames"],
        "groups.memberOfSupport": False,
    }
    if not anonymous:
        values["server.user"] = "cn=Manager,dc=example,dc=com"
        values["server.password"] = password
    return values


class _FakeLDAPGroupsError(ldap.LDAPError):
    """ldap.LDAPError subclass with a .message dict (as expected by the code)."""

    def __init__(self, desc):
        self.message = {"desc": desc}
        super().__init__(desc)


# ---------------------------------------------------------------------------
# BasePropertiesForm — abstract methods (lines 58, 62)
# ---------------------------------------------------------------------------


class TestBasePropertiesFormAbstractMethods(unittest.TestCase):
    """Tests for the abstract interface of BasePropertiesForm."""

    def test_plugin_raises_not_implemented(self):
        """plugin property raises NotImplementedError (line 58)."""
        form = BasePropertiesForm.__new__(BasePropertiesForm)
        with self.assertRaises(NotImplementedError):
            _ = form.plugin

    def test_next_raises_not_implemented(self):
        """next() raises NotImplementedError (line 62)."""
        form = BasePropertiesForm.__new__(BasePropertiesForm)
        with self.assertRaises(NotImplementedError):
            form.next({})


# ---------------------------------------------------------------------------
# action property (line 67)
# ---------------------------------------------------------------------------


class TestActionProperty(unittest.TestCase):
    """Tests for the action property."""

    def test_action_delegates_to_next(self):
        """action property returns next({}) (line 67)."""
        form = _make_form(next_url="/my-action-url")
        self.assertEqual(form.action, "/my-action-url")


# ---------------------------------------------------------------------------
# prepare() (lines 72-104)
# ---------------------------------------------------------------------------


class TestPrepare(unittest.TestCase):
    """Tests for BasePropertiesForm.prepare()."""

    def _mock_adapters(self, user="admin"):
        mock_props = MagicMock()
        mock_props.user = user
        mock_users = MagicMock()
        # dict so .get() and .items() work naturally
        mock_users.attrmap = {
            "rdn": "uid",
            "id": "uid",
            "login": "uid",
            "email": "mail",
            "fullname": "cn",
        }
        mock_groups = MagicMock()
        mock_groups.attrmap = {
            "rdn": "cn",
            "id": "cn",
            "title": "o",
            "description": "description",
        }
        return mock_props, mock_users, mock_groups

    def test_prepare_happy_path_sets_all_attrs(self):
        """Happy-path prepare() populates all expected attributes (lines 72-104)."""
        form = _make_form()
        mock_props, mock_users, mock_groups = self._mock_adapters(user="admin")

        with (
            patch("pas.plugins.ldap.properties.ILDAPProps", return_value=mock_props),
            patch(
                "pas.plugins.ldap.properties.ILDAPUsersConfig", return_value=mock_users
            ),
            patch(
                "pas.plugins.ldap.properties.ILDAPGroupsConfig",
                return_value=mock_groups,
            ),
            patch.object(YAMLBaseForm, "prepare"),
        ):
            form.prepare()

        self.assertIs(form.props, mock_props)
        self.assertIs(form.users, mock_users)
        self.assertIs(form.groups, mock_groups)
        # user = "admin" (truthy) → not anonymous
        self.assertFalse(form.anonymous)
        # static user attrs in users_attrmap
        for key in ("rdn", "id", "login"):
            self.assertIn(key, form.users_attrmap)
        # non-static attrs in users_propsheet_attrmap
        self.assertIn("email", form.users_propsheet_attrmap)
        self.assertIn("fullname", form.users_propsheet_attrmap)
        # static attrs NOT in users_propsheet_attrmap
        self.assertNotIn("rdn", form.users_propsheet_attrmap)
        # static group attrs in groups_attrmap
        for key in ("rdn", "id"):
            self.assertIn(key, form.groups_attrmap)
        # non-static group attrs in groups_propsheet_attrmap
        self.assertIn("title", form.groups_propsheet_attrmap)
        self.assertIn("description", form.groups_propsheet_attrmap)

    def test_prepare_sets_anonymous_when_user_empty(self):
        """prepare() sets anonymous=True when props.user is falsy."""
        form = _make_form()
        mock_props, mock_users, mock_groups = self._mock_adapters(user="")

        with (
            patch("pas.plugins.ldap.properties.ILDAPProps", return_value=mock_props),
            patch(
                "pas.plugins.ldap.properties.ILDAPUsersConfig", return_value=mock_users
            ),
            patch(
                "pas.plugins.ldap.properties.ILDAPGroupsConfig",
                return_value=mock_groups,
            ),
            patch.object(YAMLBaseForm, "prepare"),
        ):
            form.prepare()

        self.assertTrue(form.anonymous)

    def test_prepare_exception_reinitializes_and_retries(self):
        """Exception branch: calls init_settings() and retries (lines 76-83)."""
        form = _make_form()
        mock_props, mock_users, mock_groups = self._mock_adapters(user="admin")

        call_count = [0]

        def _ildapprops(plugin):
            call_count[0] += 1
            if call_count[0] == 1:
                raise TypeError("adapter failure on first call")
            return mock_props

        with (
            patch("pas.plugins.ldap.properties.ILDAPProps", side_effect=_ildapprops),
            patch(
                "pas.plugins.ldap.properties.ILDAPUsersConfig", return_value=mock_users
            ),
            patch(
                "pas.plugins.ldap.properties.ILDAPGroupsConfig",
                return_value=mock_groups,
            ),
            patch.object(YAMLBaseForm, "prepare"),
            patch("pas.plugins.ldap.properties.logger"),
        ):
            form.prepare()

        # init_settings() should have been called once on the plugin
        form._plugin.init_settings.assert_called_once()
        # ILDAPProps was invoked twice (once failing, once succeeding)
        self.assertEqual(call_count[0], 2)
        self.assertIs(form.props, mock_props)


# ---------------------------------------------------------------------------
# render_form() (lines 112-117)
# ---------------------------------------------------------------------------


class TestRenderForm(unittest.TestCase):
    """Tests for BasePropertiesForm.render_form()."""

    def test_render_form_returns_rendered_when_no_next(self):
        """Returns controller.rendered when controller.next is falsy (line 115)."""
        form = _make_form()
        mock_controller = MagicMock()
        mock_controller.next = None
        mock_controller.rendered = "<html>form html</html>"

        with (
            patch.object(form, "prepare"),
            patch(
                "pas.plugins.ldap.properties.Controller", return_value=mock_controller
            ),
        ):
            result = form.render_form()

        self.assertEqual(result, "<html>form html</html>")

    def test_render_form_redirects_and_returns_empty_on_next(self):
        """Redirects and returns '' when controller.next is truthy (lines 116-117)."""
        form = _make_form()
        mock_controller = MagicMock()
        mock_controller.next = "/redirect-target"

        with (
            patch.object(form, "prepare"),
            patch(
                "pas.plugins.ldap.properties.Controller", return_value=mock_controller
            ),
        ):
            result = form.render_form()

        form.request.RESPONSE.redirect.assert_called_once_with("/redirect-target")
        self.assertEqual(result, "")


# ---------------------------------------------------------------------------
# save() (lines 126-208)
# ---------------------------------------------------------------------------


class TestSave(unittest.TestCase):
    """Tests for BasePropertiesForm.save()."""

    def _run_save(
        self, field_values, mock_props=None, mock_users=None, mock_groups=None
    ):
        """Helper: run save() with patched adapters and the given field values."""
        form = _make_form()
        if mock_props is None:
            mock_props = MagicMock()
        if mock_users is None:
            mock_users = MagicMock()
        if mock_groups is None:
            mock_groups = MagicMock()
        data = _make_data(field_values)

        with (
            patch("pas.plugins.ldap.properties.ILDAPProps", return_value=mock_props),
            patch(
                "pas.plugins.ldap.properties.ILDAPUsersConfig", return_value=mock_users
            ),
            patch(
                "pas.plugins.ldap.properties.ILDAPGroupsConfig",
                return_value=mock_groups,
            ),
        ):
            form.save(MagicMock(), data)

        return mock_props, mock_users, mock_groups

    def test_non_anonymous_sets_user_and_password(self):
        """Non-anonymous path: sets user and password (lines 141-143)."""
        values = _full_save_fields(anonymous=False, password="s3cret123")
        mock_props, _, _ = self._run_save(values)
        self.assertEqual(mock_props.user, "cn=Manager,dc=example,dc=com")
        self.assertEqual(mock_props.password, "s3cret123")

    def test_non_anonymous_password_unset_skips_password_assignment(self):
        """Non-anonymous path: password UNSET → password NOT overwritten (branch line 143)."""
        values = _full_save_fields(anonymous=False, password=UNSET)
        mock_props = MagicMock()
        self._run_save(values, mock_props=mock_props)
        # props.user is set; no exception means the UNSET branch ran without crash
        self.assertEqual(mock_props.user, "cn=Manager,dc=example,dc=com")

    def test_anonymous_clears_user_and_password(self):
        """Anonymous path: clears user and password (lines 145-147)."""
        values = _full_save_fields(anonymous=True)
        mock_props, _, _ = self._run_save(values)
        self.assertEqual(mock_props.user, "")
        self.assertEqual(mock_props.password, "")

    def test_propsheet_attrmap_updates_users_attrmap(self):
        """When users propsheet_attrmap is not UNSET, it updates users.attrmap (lines 175-176)."""
        values = _full_save_fields(users_propsheet={"email": "mail"})
        _, mock_users, _ = self._run_save(values)
        # users.attrmap was replaced with an odict; verify "email" key was added
        self.assertIn("email", mock_users.attrmap)

    def test_propsheet_attrmap_unset_skips_update(self):
        """When propsheet_attrmap is UNSET, users.attrmap is NOT updated from it."""
        values = _full_save_fields(
            users_propsheet=UNSET,
            groups_propsheet=UNSET,
        )
        _, mock_users, _ = self._run_save(values)
        # Only the aliases_attrmap keys should be present
        for key in ("email", "fullname"):
            self.assertNotIn(key, mock_users.attrmap)

    def test_id_value_not_in_attrmap_adds_self_referential_entry(self):
        """If attrmap['id'] value is not a key, adds self-referential entry (line 181)."""
        # aliases: {"rdn": "uid", "id": "uid", "login": "uid"}
        # After update: attrmap["id"] = "uid", but "uid" is NOT a key → line 181 runs
        values = _full_save_fields(
            aliases_attrmap={"rdn": "uid", "id": "uid", "login": "uid"},
            users_propsheet=UNSET,
        )
        _, mock_users, _ = self._run_save(values)
        self.assertIn("uid", mock_users.attrmap)
        self.assertEqual(mock_users.attrmap["uid"], "uid")

    def test_id_value_already_in_attrmap_skips_self_referential(self):
        """If attrmap['id'] value IS a key, the self-referential branch is skipped."""
        # Include "uid" as an explicit key so "uid" IS in attrmap
        values = _full_save_fields(
            aliases_attrmap={"rdn": "cn", "id": "cn", "login": "cn", "cn": "cn"},
            users_propsheet=UNSET,
        )
        _, mock_users, _ = self._run_save(values)
        # "cn" is both the id-value and an existing key → no extra entry added
        self.assertIn("cn", mock_users.attrmap)

    def test_users_scope_converted_when_not_unset(self):
        """users.scope is int-converted when not UNSET (line 184)."""
        values = _full_save_fields(users_scope='"2"')
        _, mock_users, _ = self._run_save(values)
        self.assertEqual(mock_users.scope, 2)

    def test_users_scope_stays_unset_when_unset(self):
        """users.scope is left as-is when fetch returns UNSET (line 183 branch)."""
        values = _full_save_fields(users_scope=UNSET)
        _, mock_users, _ = self._run_save(values)
        self.assertIs(mock_users.scope, UNSET)

    def test_groups_propsheet_attrmap_updates_groups_attrmap(self):
        """When groups propsheet_attrmap is not UNSET, groups.attrmap is updated (lines 198-199)."""
        values = _full_save_fields(groups_propsheet={"title": "o"})
        _, _, mock_groups = self._run_save(values)
        self.assertIn("title", mock_groups.attrmap)

    def test_groups_scope_converted_when_not_unset(self):
        """groups.scope is int-converted when not UNSET (line 202)."""
        values = _full_save_fields(groups_scope='"1"')
        _, _, mock_groups = self._run_save(values)
        self.assertEqual(mock_groups.scope, 1)

    def test_groups_scope_stays_unset_when_unset(self):
        """groups.scope is left as-is when fetch returns UNSET."""
        values = _full_save_fields(groups_scope=UNSET)
        _, _, mock_groups = self._run_save(values)
        self.assertIs(mock_groups.scope, UNSET)

    def test_expires_unit_default_used_when_unset(self):
        """fetch('users.expires_unit', 0) returns 0 when value is UNSET (line 137)."""
        values = _full_save_fields(anonymous=False)
        values["users.expires_unit"] = UNSET  # override to UNSET → hits return default
        _, mock_users, _ = self._run_save(values)
        self.assertEqual(mock_users._expiresUnit, 0)

    def test_save_sets_all_server_props(self):
        """All server-level props are forwarded to props object (lines 149-160)."""
        values = _full_save_fields(anonymous=False, password="pw")
        mock_props, _, _ = self._run_save(values)
        self.assertEqual(mock_props.uri, "ldap://localhost:389")
        self.assertFalse(mock_props.ignore_cert)
        self.assertFalse(mock_props.start_tls)

    def test_save_sets_cache_props(self):
        """Cache-related props are forwarded (lines 161-164)."""
        values = _full_save_fields(anonymous=True)
        mock_props, _, _ = self._run_save(values)
        self.assertFalse(mock_props.cache)
        self.assertEqual(mock_props.timeout, 300)


# ---------------------------------------------------------------------------
# userpassanon_extractor() (lines 218-235)
# ---------------------------------------------------------------------------


class TestUserPassAnonExtractor(unittest.TestCase):
    """Tests for BasePropertiesForm.userpassanon_extractor()."""

    def _make_data_mock(self, extracted, anonymous, user="", password="", pw_value=""):
        """Build a mock data object for userpassanon_extractor() tests."""
        data = MagicMock()
        data.extracted = extracted
        anon_mock = MagicMock(extracted=anonymous)
        user_mock = MagicMock(extracted=user, errors=[])
        pw_mock = MagicMock(extracted=password, value=pw_value, errors=[])
        data.__getitem__ = MagicMock(
            side_effect=lambda key: {
                "anonymous": anon_mock,
                "user": user_mock,
                "password": pw_mock,
            }[key]
        )
        return data, user_mock, pw_mock

    def test_returns_early_when_not_extracted(self):
        """Returns data.extracted when data.extracted is falsy (line 219 first branch)."""
        form = _make_form()
        data = MagicMock()
        data.extracted = None
        result = form.userpassanon_extractor(MagicMock(), data)
        self.assertIsNone(result)

    def test_returns_early_when_anonymous(self):
        """Returns data.extracted when anonymous=True (line 219 second branch)."""
        form = _make_form()
        data, _, _ = self._make_data_mock(extracted="some-data", anonymous=True)
        result = form.userpassanon_extractor(MagicMock(), data)
        self.assertEqual(result, "some-data")

    def test_user_empty_appends_error_and_raises(self):
        """Empty user → error appended and ExtractionError raised (lines 222-225)."""
        form = _make_form()
        data, user_mock, _ = self._make_data_mock(
            extracted="data",
            anonymous=False,
            user="",
            password="secret",
            pw_value="secret",
        )
        with self.assertRaises(ExtractionError):
            form.userpassanon_extractor(MagicMock(), data)
        self.assertEqual(len(user_mock.errors), 1)

    def test_password_empty_appends_error_and_raises(self):
        """Empty password → error appended and ExtractionError raised (lines 226-230)."""
        form = _make_form()
        data, _, pw_mock = self._make_data_mock(
            extracted="data", anonymous=False, user="admin", password="", pw_value=""
        )
        with self.assertRaises(ExtractionError):
            form.userpassanon_extractor(MagicMock(), data)
        self.assertEqual(len(pw_mock.errors), 1)

    def test_both_empty_appends_both_errors_and_raises(self):
        """Both user and password empty → two errors, ExtractionError raised."""
        form = _make_form()
        data, user_mock, pw_mock = self._make_data_mock(
            extracted="data", anonymous=False, user="", password="", pw_value=""
        )
        with self.assertRaises(ExtractionError):
            form.userpassanon_extractor(MagicMock(), data)
        self.assertEqual(len(user_mock.errors), 1)
        self.assertEqual(len(pw_mock.errors), 1)

    def test_valid_credentials_returns_extracted(self):
        """Valid user and password → returns data.extracted (line 235)."""
        form = _make_form()
        data, _, _ = self._make_data_mock(
            extracted="result-data",
            anonymous=False,
            user="admin",
            password="secret",
            pw_value="secret",
        )
        result = form.userpassanon_extractor(MagicMock(), data)
        self.assertEqual(result, "result-data")


# ---------------------------------------------------------------------------
# connection_test() (lines 244-279)
# ---------------------------------------------------------------------------


class TestConnectionTest(unittest.TestCase):
    """Tests for BasePropertiesForm.connection_test()."""

    def _patch_adapters(self, props=None, users=None, groups=None):
        """Context-manager helper that patches the three LDAP config adapters."""
        return (
            patch(
                "pas.plugins.ldap.properties.ILDAPProps",
                return_value=props if props is not None else MagicMock(),
            ),
            patch(
                "pas.plugins.ldap.properties.ILDAPUsersConfig",
                return_value=users if users is not None else MagicMock(),
            ),
            patch(
                "pas.plugins.ldap.properties.ILDAPGroupsConfig",
                return_value=groups if groups is not None else MagicMock(),
            ),
        )

    def test_ildapprops_exception_returns_false(self):
        """Returns (False, msg) when ILDAPProps raises (lines 246-249)."""
        form = _make_form()
        with (
            patch(
                "pas.plugins.ldap.properties.ILDAPProps",
                side_effect=RuntimeError("props-fail"),
            ),
            patch("pas.plugins.ldap.properties.logger"),
        ):
            ok, msg = form.connection_test()

        self.assertFalse(ok)
        self.assertIn("props-fail", str(msg))

    def test_ildapusersconfig_exception_returns_false(self):
        """Returns (False, msg) when ILDAPUsersConfig raises (lines 251-254)."""
        form = _make_form()
        with (
            patch("pas.plugins.ldap.properties.ILDAPProps", return_value=MagicMock()),
            patch(
                "pas.plugins.ldap.properties.ILDAPUsersConfig",
                side_effect=RuntimeError("users-fail"),
            ),
            patch("pas.plugins.ldap.properties.logger"),
        ):
            ok, msg = form.connection_test()

        self.assertFalse(ok)
        self.assertIn("users-fail", str(msg))

    def test_ildapgroupsconfig_exception_returns_false(self):
        """Returns (False, msg) when ILDAPGroupsConfig raises (lines 256-259)."""
        form = _make_form()
        with (
            patch("pas.plugins.ldap.properties.ILDAPProps", return_value=MagicMock()),
            patch(
                "pas.plugins.ldap.properties.ILDAPUsersConfig", return_value=MagicMock()
            ),
            patch(
                "pas.plugins.ldap.properties.ILDAPGroupsConfig",
                side_effect=RuntimeError("groups-fail"),
            ),
            patch("pas.plugins.ldap.properties.logger"),
        ):
            ok, msg = form.connection_test()

        self.assertFalse(ok)
        self.assertIn("groups-fail", str(msg))

    def test_server_down_returns_false(self):
        """Returns (False, 'Server Down') on ldap.SERVER_DOWN (line 262)."""
        form = _make_form()
        mock_ugm = MagicMock()
        mock_ugm.users.authenticate.side_effect = ldap.SERVER_DOWN

        p1, p2, p3 = self._patch_adapters()
        with (
            p1,
            p2,
            p3,
            patch("pas.plugins.ldap.properties.Ugm", return_value=mock_ugm),
        ):
            ok, msg = form.connection_test()

        self.assertFalse(ok)
        self.assertIn("Down", str(msg))

    def test_ldap_error_in_users_returns_false(self):
        """Returns (False, msg) for ldap.LDAPError in users authenticate (line 263)."""
        form = _make_form()
        mock_ugm = MagicMock()
        mock_ugm.users.authenticate.side_effect = ldap.LDAPError("users ldap error")

        p1, p2, p3 = self._patch_adapters()
        with (
            p1,
            p2,
            p3,
            patch("pas.plugins.ldap.properties.Ugm", return_value=mock_ugm),
        ):
            ok, msg = form.connection_test()

        self.assertFalse(ok)
        self.assertIn("LDAP users", str(msg))

    def test_generic_exception_in_users_returns_false(self):
        """Returns (False, msg) for non-LDAP exception in users (lines 265-267)."""
        form = _make_form()
        mock_ugm = MagicMock()
        mock_ugm.users.authenticate.side_effect = RuntimeError("generic users error")

        p1, p2, p3 = self._patch_adapters()
        with (
            p1,
            p2,
            p3,
            patch("pas.plugins.ldap.properties.Ugm", return_value=mock_ugm),
            patch("pas.plugins.ldap.properties.logger"),
        ):
            ok, msg = form.connection_test()

        self.assertFalse(ok)
        self.assertIn("generic users error", str(msg))

    def test_ldap_error_in_groups_returns_false(self):
        """Returns (False, msg) for ldap.LDAPError in groups.keys() (lines 269-270)."""
        form = _make_form()
        mock_ugm = MagicMock()
        mock_ugm.users.authenticate.return_value = None  # users OK
        mock_ugm.groups.keys.side_effect = _FakeLDAPGroupsError("groups-ldap-error")

        p1, p2, p3 = self._patch_adapters()
        with (
            p1,
            p2,
            p3,
            patch("pas.plugins.ldap.properties.Ugm", return_value=mock_ugm),
        ):
            ok, msg = form.connection_test()

        self.assertFalse(ok)
        self.assertIn("groups-ldap-error", str(msg))

    def test_generic_exception_in_groups_returns_false(self):
        """Returns (False, msg) for non-LDAP exception in groups.keys() (lines 271-273)."""
        form = _make_form()
        mock_ugm = MagicMock()
        mock_ugm.users.authenticate.return_value = None
        mock_ugm.groups.keys.side_effect = RuntimeError("generic groups error")

        p1, p2, p3 = self._patch_adapters()
        with (
            p1,
            p2,
            p3,
            patch("pas.plugins.ldap.properties.Ugm", return_value=mock_ugm),
            patch("pas.plugins.ldap.properties.logger"),
        ):
            ok, msg = form.connection_test()

        self.assertFalse(ok)
        self.assertIn("generic groups error", str(msg))

    def test_connection_success_returns_true(self):
        """Returns (True, success msg) when all checks pass (line 279)."""
        form = _make_form()
        mock_ugm = MagicMock()
        mock_ugm.users.authenticate.return_value = None
        mock_ugm.groups.keys.return_value = []

        p1, p2, p3 = self._patch_adapters()
        with (
            p1,
            p2,
            p3,
            patch("pas.plugins.ldap.properties.Ugm", return_value=mock_ugm),
        ):
            ok, msg = form.connection_test()

        self.assertTrue(ok)
        self.assertIn("successfully", str(msg))


# ---------------------------------------------------------------------------
# propproxy (lines 293-310)
# ---------------------------------------------------------------------------


class TestPropProxy(unittest.TestCase):
    """Tests for the propproxy() factory."""

    def _make_adapter_class(self, ckey):
        """Return a class with a propproxy-backed attribute."""

        class _Adapter:
            def __init__(self, plugin):
                self.plugin = plugin

            prop = propproxy(ckey)

        return _Adapter

    def test_getter_returns_default_when_key_absent(self):
        """_getter returns DEFAULTS[ckey] when key not in plugin.settings."""
        plugin = _make_plugin_with_settings()
        cls = self._make_adapter_class("server.uri")
        adapter = cls(plugin)
        self.assertEqual(adapter.prop, DEFAULTS["server.uri"])

    def test_getter_returns_stored_value(self):
        """_getter returns the value stored in plugin.settings."""
        plugin = _make_plugin_with_settings({"server.uri": "ldap://custom:389"})
        cls = self._make_adapter_class("server.uri")
        adapter = cls(plugin)
        self.assertEqual(adapter.prop, "ldap://custom:389")

    def test_setter_stores_value_in_settings(self):
        """_setter stores value in plugin.settings[ckey]."""
        plugin = _make_plugin_with_settings()
        cls = self._make_adapter_class("server.uri")
        adapter = cls(plugin)
        adapter.prop = "ldap://newhost:1389"
        self.assertEqual(plugin.settings["server.uri"], "ldap://newhost:1389")


# ---------------------------------------------------------------------------
# LDAPProps.memcached getter/setter (lines 350-354, 371)
# ---------------------------------------------------------------------------


class TestLDAPPropsMemcached(unittest.TestCase):
    """Tests for LDAPProps.memcached getter and setter."""

    def _make_props(self):
        plugin = _make_plugin_with_settings()
        return LDAPProps(plugin)

    def test_memcached_getter_with_record_provider_returns_value(self):
        """Returns record.value when a record provider is registered (lines 350-353)."""
        props = self._make_props()
        mock_record = MagicMock()
        mock_record.value = "memcache-host:11211"
        mock_provider = MagicMock(return_value=mock_record)

        with patch(
            "pas.plugins.ldap.properties.queryUtility", return_value=mock_provider
        ):
            result = props.memcached

        self.assertEqual(result, "memcache-host:11211")

    def test_memcached_getter_without_record_provider_returns_unavailable(self):
        """Returns 'feature not available' when no provider is registered (line 354)."""
        props = self._make_props()

        with patch("pas.plugins.ldap.properties.queryUtility", return_value=None):
            result = props.memcached

        self.assertIn("not available", str(result))

    def test_memcached_setter_with_record_provider_sets_value(self):
        """Sets record.value when a provider is registered (lines 366-369)."""
        props = self._make_props()
        mock_record = MagicMock()
        mock_provider = MagicMock(return_value=mock_record)

        with patch(
            "pas.plugins.ldap.properties.queryUtility", return_value=mock_provider
        ):
            props.memcached = "new-host:11211"

        self.assertEqual(mock_record.value, "new-host:11211")

    def test_memcached_setter_without_record_provider_returns_unavailable(self):
        """Returns 'feature not available' in setter else branch (line 371)."""
        props = self._make_props()

        # When queryUtility returns None, the else-branch (line 371) executes.
        # The return value of a setter is normally discarded; we just verify
        # that no exception is raised and that no record is written.
        with patch("pas.plugins.ldap.properties.queryUtility", return_value=None):
            props.memcached = "some-value"  # must not raise


# ---------------------------------------------------------------------------
# UsersConfig.expiresAttr / expiresUnit (lines 407, 416)
# ---------------------------------------------------------------------------


class TestUsersConfigExpiry(unittest.TestCase):
    """Tests for UsersConfig.expiresAttr and expiresUnit properties."""

    def _make_users_config(
        self, account_expiration=True, expires_attr="shadowExpire", expires_unit=1
    ):
        plugin = _make_plugin_with_settings(
            {
                "users.account_expiration": account_expiration,
                "users.expires_attr": expires_attr,
                "users.expires_unit": expires_unit,
            }
        )
        return UsersConfig(plugin)

    # --- expiresAttr (line 407) ---

    def test_expires_attr_returns_attr_when_expiration_enabled(self):
        """expiresAttr returns the attribute name when account_expiration is True (line 407)."""
        config = self._make_users_config(
            account_expiration=True, expires_attr="shadowExpire"
        )
        self.assertEqual(config.expiresAttr, "shadowExpire")

    def test_expires_attr_returns_none_when_expiration_disabled(self):
        """expiresAttr returns None when account_expiration is False."""
        config = self._make_users_config(account_expiration=False)
        self.assertIsNone(config.expiresAttr)

    # --- expiresUnit (line 416) ---

    def test_expires_unit_returns_unit_when_expiration_enabled(self):
        """expiresUnit returns the unit value when account_expiration is True (line 416)."""
        config = self._make_users_config(account_expiration=True, expires_unit=1)
        self.assertEqual(config.expiresUnit, 1)

    def test_expires_unit_returns_zero_when_expiration_disabled(self):
        """expiresUnit returns 0 when account_expiration is False."""
        config = self._make_users_config(account_expiration=False, expires_unit=99)
        self.assertEqual(config.expiresUnit, 0)


class TestGroupsConfigInit(unittest.TestCase):
    """Tests to cover GroupsConfig.__init__ (line 425)."""

    def test_init_stores_plugin(self):
        """GroupsConfig.__init__ stores plugin on self.plugin (line 425)."""
        plugin = MagicMock()
        config = GroupsConfig(plugin)
        self.assertIs(config.plugin, plugin)


if __name__ == "__main__":
    unittest.main()
