# -*- coding: utf-8 -*-
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
from pas.plugins.ldap.defaults import DEFAULTS
from pas.plugins.ldap.interfaces import ICacheSettingsRecordProvider
from pas.plugins.ldap.interfaces import ILDAPPlugin
from Products.Five import BrowserView
from yafowil import loader  # noqa: F401
from yafowil.base import ExtractionError
from yafowil.base import UNSET
from yafowil.controller import Controller
from yafowil.yaml import parse_from_YAML
from zope.component import adapter
from zope.component import queryUtility
from zope.i18nmessageid import MessageFactory
from zope.interface import implementer

import ldap
import logging


logger = logging.getLogger("pas.plugins.ldap")
_ = MessageFactory("pas.plugins.ldap")

_marker = dict()


class BasePropertiesForm(BrowserView):
    scope_vocab = [
        (str(BASE), "BASE"),
        (str(ONELEVEL), "ONELEVEL"),
        (str(SUBTREE), "SUBTREE"),
    ]
    static_attrs_users = ["rdn", "id", "login"]
    static_attrs_groups = ["rdn", "id"]

    @property
    def plugin(self):
        raise NotImplementedError()

    def next(self, request):
        raise NotImplementedError()

    @property
    def action(self):
        return self.next({})

    def form(self):
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
        return u""

    def save(self, widget, data):
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
        # TODO: later
        # props.start_tls = fetch('server.start_tls')
        # props.tls_cacertfile = fetch('server.tls_cacertfile')
        # props.tls_cacertdir = fetch('server.tls_cacertdir')
        # props.tls_clcertfile = fetch('server.tls_clcertfile')
        # props.tls_clkeyfile = fetch('server.tls_clkeyfile')
        # props.retry_max = fetch(at('server.retry_max')
        # props.retry_delay = fetch('server.retry_delay')
        props.page_size = fetch("server.page_size")
        props.cache = fetch("cache.cache")
        props.memcached = fetch("cache.memcached")
        props.timeout = fetch("cache.timeout")
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
        if users.attrmap['id'] not in users.attrmap:
            users.attrmap[users.attrmap['id']] = users.attrmap['id']
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
            ugm.users
        except ldap.SERVER_DOWN:
            return False, _("Server Down")
        except ldap.LDAPError as e:
            return False, _("LDAP users; ") + str(e)
        except Exception as e:
            logger.exception("Non-LDAP error while connection test!")
            return False, _("Exception in Users; ") + str(e)
        try:
            ugm.groups
        except ldap.LDAPError as e:
            return False, _("LDAP Users ok, but groups not; ") + e.message["desc"]
        except Exception as e:
            logger.exception("Non-LDAP error while connection test!")
            return False, _("Exception in Groups; ") + str(e)
        return True, "Connection, users- and groups-access tested successfully."


def propproxy(ckey):
    def _getter(context):
        value = context.plugin.settings.get(ckey, DEFAULTS[ckey])
        return value

    def _setter(context, value):
        context.plugin.settings[ckey] = value

    return property(_getter, _setter)


@implementer(ILDAPProps)
@adapter(ILDAPPlugin)
class LDAPProps(object):
    def __init__(self, plugin):
        self.plugin = plugin

    # XXX: Later
    tls_cacertfile = ""
    tls_cacertdir = ""
    tls_clcertfile = ""
    tls_clkeyfile = ""
    retry_max = 3
    retry_delay = 5

    uri = propproxy("server.uri")
    user = propproxy("server.user")
    password = propproxy("server.password")
    start_tls = propproxy("server.start_tls")
    ignore_cert = propproxy("server.ignore_cert")
    page_size = propproxy("server.page_size")
    cache = propproxy("cache.cache")
    timeout = propproxy("cache.timeout")

    @property
    def memcached(self):
        recordProvider = queryUtility(ICacheSettingsRecordProvider)
        if recordProvider is not None:
            record = recordProvider()
            return record.value
        return u"feature not available"

    @memcached.setter
    def memcached(self, value):
        recordProvider = queryUtility(ICacheSettingsRecordProvider)
        if recordProvider is not None:
            record = recordProvider()
            record.value = value
        else:
            return u"feature not available"

    binary_attributes = BINARY_DEFAULTS
    multivalued_attributes = MULTIVALUED_DEFAULTS


@implementer(ILDAPUsersConfig)
@adapter(ILDAPPlugin)
class UsersConfig(object):
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
        return self.account_expiration and self._expiresAttr or None

    @property
    def expiresUnit(self):
        return self.account_expiration and self._expiresUnit or 0


@implementer(ILDAPGroupsConfig)
@adapter(ILDAPPlugin)
class GroupsConfig(object):
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
