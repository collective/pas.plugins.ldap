"""Properties and configuration for the LDAP plugin."""

from .defaults import DEFAULTS
from .interfaces import ICacheSettingsRecordProvider
from .interfaces import ILDAPPlugin
from node.ext.ldap.interfaces import ILDAPGroupsConfig
from node.ext.ldap.interfaces import ILDAPProps
from node.ext.ldap.interfaces import ILDAPUsersConfig
from node.ext.ldap.properties import BINARY_DEFAULTS
from node.ext.ldap.properties import MULTIVALUED_DEFAULTS
from node.ext.ldap.scope import BASE
from node.ext.ldap.scope import ONELEVEL
from node.ext.ldap.scope import SUBTREE
from node.ext.ldap.ugm import Ugm
from odict import odict
from pas.plugins.ldap import _
from pas.plugins.ldap import logger
from Products.Five import BrowserView
from yafowil import loader  # noqa: F401
from yafowil.base import ExtractionError
from yafowil.base import UNSET
from yafowil.controller import Controller
from yafowil.yaml import parse_from_YAML
from zope.component import adapter
from zope.component import queryUtility
from zope.interface import implementer

import ldap

_marker = dict()


class BasePropertiesForm(BrowserView):
    """Base class for LDAP properties forms."""

    # scope vocabulary, used in the form to provide options for the LDAP search
    # scope. The values represent the respective LDAP search scope constants.
    scope_vocab = [
        (str(BASE), _("BASE")),
        (str(ONELEVEL), _("ONELEVEL")),
        (str(SUBTREE), _("SUBTREE")),
    ]
    # account expiration unit vocabulary, used in the form to provide options
    # for the expiration unit of user accounts. The values represent the number
    # of seconds in the respective unit.
    account_expiration_unit_vocab = [
        (int(0), _("Days since Epoch")),
        (int(1), _("Seconds since epoch")),
    ]
    static_attrs_users = ["rdn", "id", "login"]
    static_attrs_groups = ["rdn", "id"]

    @property
    def plugin(self):
        """Get the LDAP plugin instance."""
        raise NotImplementedError()

    def next(self, request):
        """Get the next URL for redirection after form submission."""
        raise NotImplementedError()

    @property
    def action(self):
        """Get the form action URL."""
        return self.next({})

    def form(self):
        """Render the LDAP properties form.

        Returns:
            str: Rendered HTML of the form
        """
        # make configuration data available on form context
        try:
            self.props = ILDAPProps(self.plugin)
            self.users = ILDAPUsersConfig(self.plugin)
            self.groups = ILDAPGroupsConfig(self.plugin)
        except Exception:
            msg = "Problems getting the configuration adapters, re-initialize!"
            logger.exception(msg)
            self.plugin.init_settings()
        self.anonymous = not self.props.user
        # prepare users data on form context
        self.users_attrmap = odict()
        for key in self.static_attrs_users:
            self.users_attrmap[key] = self.users.attrmap.get(key)
        self.users_propsheet_attrmap = odict()
        for key, value in self.users.attrmap.items():
            if key in self.static_attrs_users:
                continue
            self.users_propsheet_attrmap[key] = value
        # prepare groups data on form context
        self.groups_attrmap = odict()
        for key in self.static_attrs_groups:
            self.groups_attrmap[key] = self.groups.attrmap.get(key)
        self.groups_propsheet_attrmap = odict()
        for key, value in self.groups.attrmap.items():
            if key in self.static_attrs_groups:
                continue
            self.groups_propsheet_attrmap[key] = value
        # handle form
        form = parse_from_YAML("pas.plugins.ldap:properties.yaml", self, _)
        controller = Controller(form, self.request)
        if not controller.next:
            return controller.rendered
        self.request.RESPONSE.redirect(controller.next)
        return ""

    def save(self, widget, data):
        """Save the LDAP properties form.

        Args:
            widget (Widget): Widget instance
            data (Data): Data extracted from the form
        """
        props = ILDAPProps(self.plugin)
        users = ILDAPUsersConfig(self.plugin)
        groups = ILDAPGroupsConfig(self.plugin)

        def fetch(name, default=UNSET):
            name = "ldapsettings.%s" % name
            __traceback_info__ = name
            val = data.fetch(name).extracted
            if default is UNSET:
                return val
            if val is UNSET:
                return default
            return val

        props.uri = fetch("server.uri")

        if not fetch("server.anonymous"):
            props.user = fetch("server.user")
            password = fetch("server.password")
            if password is not UNSET:
                props.password = password
        else:
            props.user = ""
            props.password = ""
        props.ignore_cert = fetch("server.ignore_cert")
        props.start_tls = fetch("server.start_tls")
        props.tls_cacertfile = fetch("server.tls_cacertfile")
        props.tls_cacertdir = fetch("server.tls_cacertdir")
        props.tls_clcertfile = fetch("server.tls_clcertfile")
        props.tls_clkeyfile = fetch("server.tls_clkeyfile")
        # TODO: later
        # props.retry_max = fetch(at('server.retry_max')
        # props.retry_delay = fetch('server.retry_delay')
        props.page_size = fetch("server.page_size")
        props.conn_timeout = fetch("server.conn_timeout")
        props.op_timeout = fetch("server.op_timeout")
        props.cache = fetch("cache.cache")
        props.memcached = fetch("cache.memcached")
        props.timeout = fetch("cache.timeout")

        props.roles = fetch(
            "users.roles"
        )  # a server wide variable, but related to user

        users.baseDN = fetch("users.dn")
        # build attrmap from static keys and dynamic keys inputs
        users.attrmap = odict()
        users.attrmap.update(fetch("users.aliases_attrmap"))
        users_propsheet_attrmap = fetch("users.propsheet_attrmap")
        if users_propsheet_attrmap is not UNSET:
            users.attrmap.update(users_propsheet_attrmap)
        # we expect to always have the id key mapped under the same name in the
        # propertysheet. this would be set implicit on LDAPPrincipal init, but
        # to avoid a write on read, we do it here.
        if users.attrmap["id"] not in users.attrmap:
            users.attrmap[users.attrmap["id"]] = users.attrmap["id"]
        users.scope = fetch("users.scope")
        if users.scope is not UNSET:
            users.scope = int(users.scope.strip('"'))
        users.queryFilter = fetch("users.query")
        objectClasses = fetch("users.object_classes")
        users.objectClasses = objectClasses
        users.memberOfSupport = fetch("users.memberOfSupport")
        users.recursiveGroups = fetch("users.recursiveGroups")
        users.memberOfExternalGroupDNs = fetch("users.memberOfExternalGroupDNs")
        users.account_expiration = fetch("users.account_expiration")
        users._expiresAttr = fetch("users.expires_attr")
        users._expiresUnit = int(fetch("users.expires_unit", 0))
        groups.baseDN = fetch("groups.dn")
        groups.attrmap = odict()
        groups.attrmap.update(fetch("groups.aliases_attrmap"))
        groups_propsheet_attrmap = fetch("groups.propsheet_attrmap")
        if groups_propsheet_attrmap is not UNSET:
            groups.attrmap.update(groups_propsheet_attrmap)
        groups.scope = fetch("groups.scope")
        if groups.scope is not UNSET:
            groups.scope = int(groups.scope.strip('"'))
        groups.queryFilter = fetch("groups.query")
        objectClasses = fetch("groups.object_classes")
        groups.objectClasses = objectClasses
        groups.memberOfSupport = fetch("groups.memberOfSupport")
        groups.recursiveGroups = False
        groups.memberOfExternalGroupDNs = []

    def userpassanon_extractor(self, widget, data):
        """Extract the user, password and anonymous values from
        the form data.

        Args:
            widget (Widget): Widget instance
            data (Data): Data extracted from the form
        """
        if not data.extracted or data["anonymous"].extracted:
            return data.extracted
        has_error = False
        if not data["user"].extracted:
            error = ExtractionError(
                _("Username is required for non-anonymous connections.")
            )
            data["user"].errors.append(error)
            has_error = True
        if not data["password"].extracted and not data["password"].value:
            error = ExtractionError(
                _("Password is required for non-anonymous connections.")
            )
            data["password"].errors.append(error)
            has_error = True
        if has_error:
            raise ExtractionError(_("User/Password are required if not anonymous."))
        return data.extracted

    def connection_test(self):
        """Test the LDAP connection.

        Returns:
            tuple: A tuple containing a boolean indicating success and
            a message string.
        """
        try:
            props = ILDAPProps(self.plugin)
        except Exception as e:
            msg = _("Non-LDAP error while getting ILDAPProps!")
            logger.exception(msg)
            return False, msg + str(e)
        try:
            users = ILDAPUsersConfig(self.plugin)
        except Exception as e:
            msg = _("Non-LDAP error while getting ILDAPUsersConfig!")
            logger.exception(msg)
            return False, msg + str(e)
        try:
            groups = ILDAPGroupsConfig(self.plugin)
        except Exception as e:
            msg = _("Non-LDAP error while getting ILDAPGroupsConfig!")
            logger.exception(msg)
            return False, msg + str(e)
        try:
            ugm = Ugm("test", props=props, ucfg=users, gcfg=groups)
            ugm.users.authenticate("foo", "bar")
        except ldap.SERVER_DOWN:
            return False, _("Server Down")
        except ldap.LDAPError as e:
            return False, _("LDAP users; ") + str(e)
        except Exception as e:
            logger.exception("Non-LDAP error while connection test!")
            return False, _("Exception in Users; ") + str(e)
        try:
            ugm.groups.keys()
        except ldap.LDAPError as e:
            return False, _("LDAP Users ok, but groups not; ") + e.message["desc"]
        except Exception as e:
            logger.exception("Non-LDAP error while connection test!")
            return False, _("Exception in Groups; ") + str(e)
        return True, _("Connection, users- and groups-access tested successfully.")


def propproxy(ckey):
    """Create a property proxy for LDAP plugin settings.

    Args:
        ckey (str): The key for the LDAP plugin setting.
    """

    def _getter(context):
        """Get a property proxy for LDAP plugin settings

        Args:
            context (object): Context object

        Returns:
            object: The value of the LDAP plugin setting for the given key.
        """
        value = context.plugin.settings.get(ckey, DEFAULTS[ckey])
        return value

    def _setter(context, value):
        """Set a property proxy for LDAP plugin settings

        Args:
            context (object): Context object
            value (object): Value to set for the LDAP plugin setting.
        """
        context.plugin.settings[ckey] = value

    return property(_getter, _setter)


@implementer(ILDAPProps)
@adapter(ILDAPPlugin)
class LDAPProps:
    """Properties for LDAP plugin."""

    def __init__(self, plugin):
        self.plugin = plugin

    # XXX: Later
    retry_max = 3
    retry_delay = 5

    uri = propproxy("server.uri")
    user = propproxy("server.user")
    roles = propproxy("server.roles")
    password = propproxy("server.password")
    start_tls = propproxy("server.start_tls")
    ignore_cert = propproxy("server.ignore_cert")
    start_tls = propproxy("server.start_tls")
    tls_cacertfile = propproxy("server.tls_cacertfile")
    tls_cacertdir = propproxy("server.tls_cacertdir")
    tls_clcertfile = propproxy("server.tls_clcertfile")
    tls_clkeyfile = propproxy("server.tls_clkeyfile")

    page_size = propproxy("server.page_size")
    conn_timeout = propproxy("server.conn_timeout")
    op_timeout = propproxy("server.op_timeout")
    cache = propproxy("cache.cache")
    timeout = propproxy("cache.timeout")

    @property
    def memcached(self):
        """Get the memcached setting.

        Returns:
            str: The memcached setting value or a message if the feature
            is not available.
        """
        recordProvider = queryUtility(ICacheSettingsRecordProvider)
        if recordProvider is not None:
            record = recordProvider()
            return record.value
        return "feature not available"

    @memcached.setter
    def memcached(self, value):
        """Set the memcached setting.

        Args:
            value (object): Value to set for memcached setting.

        Returns:
            str: The result of setting the memcached value.
        """
        recordProvider = queryUtility(ICacheSettingsRecordProvider)
        if recordProvider is not None:
            record = recordProvider()
            record.value = value
        else:
            return "feature not available"

    binary_attributes = BINARY_DEFAULTS
    multivalued_attributes = MULTIVALUED_DEFAULTS


@implementer(ILDAPUsersConfig)
@adapter(ILDAPPlugin)
class UsersConfig:
    """Configuration for LDAP users."""

    def __init__(self, plugin):
        self.plugin = plugin

    strict = False
    defaults = dict()
    baseDN = propproxy("users.baseDN")
    attrmap = propproxy("users.attrmap")
    scope = propproxy("users.scope")
    queryFilter = propproxy("users.queryFilter")
    objectClasses = propproxy("users.objectClasses")
    defaults = propproxy("users.defaults")
    memberOfSupport = propproxy("users.memberOfSupport")
    recursiveGroups = propproxy("users.recursiveGroups")
    memberOfExternalGroupDNs = propproxy("users.memberOfExternalGroupDNs")
    account_expiration = propproxy("users.account_expiration")
    _expiresAttr = propproxy("users.expires_attr")
    _expiresUnit = propproxy("users.expires_unit")

    @property
    def expiresAttr(self):
        """Expires attribute

        Returns:
            str: The expiration attribute.
        """
        return self.account_expiration and self._expiresAttr or None

    @property
    def expiresUnit(self):
        """Expires unit

        Returns:
            int: The expiration unit.
        """
        return self.account_expiration and self._expiresUnit or 0


@implementer(ILDAPGroupsConfig)
@adapter(ILDAPPlugin)
class GroupsConfig:
    """Configuration for LDAP groups."""

    def __init__(self, plugin):
        self.plugin = plugin

    strict = False
    defaults = dict()
    baseDN = propproxy("groups.baseDN")
    attrmap = propproxy("groups.attrmap")
    scope = propproxy("groups.scope")
    queryFilter = propproxy("groups.queryFilter")
    objectClasses = propproxy("groups.objectClasses")
    defaults = propproxy("groups.defaults")
    memberOfSupport = propproxy("groups.memberOfSupport")
    recursiveGroups = propproxy("groups.recursiveGroups")
    memberOfExternalGroupDNs = propproxy("groups.memberOfExternalGroupDNs")
    expiresAttr = propproxy("groups.expires_attr")
    expiresUnit = propproxy("groups.expires_unit")
