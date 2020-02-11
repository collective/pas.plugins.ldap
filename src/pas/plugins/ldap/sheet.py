# -*- coding: utf-8 -*-
from Acquisition import aq_base
from node.ext.ldap.interfaces import ILDAPGroupsConfig
from node.ext.ldap.interfaces import ILDAPUsersConfig
from Products.PlonePAS.interfaces.propertysheets import IMutablePropertySheet
from Products.PluggableAuthService.UserPropertySheet import UserPropertySheet
from zope.globalrequest import getRequest
from zope.interface import implementer

import logging


logger = logging.getLogger("pas.plugins.ldap")


@implementer(IMutablePropertySheet)
class LDAPUserPropertySheet(UserPropertySheet):
    def __init__(self, principal, plugin):
        """Instanciate LDAPUserPropertySheet.

        @param principal: user id or group id
        @param plugin: LDAPPlugin instance
        """
        # do not set any non-pickable attribute here, i.e. acquisition wrapped
        self._plugin = aq_base(plugin)
        self._properties = dict()
        self._attrmap = dict()
        self._ldapprincipal_id = principal.getId()
        if self._ldapprincipal_id in plugin.users:
            pcfg = ILDAPUsersConfig(plugin)
            self._ldapprincipal_type = "users"
        else:
            pcfg = ILDAPGroupsConfig(plugin)
            self._ldapprincipal_type = "groups"
        for k, v in pcfg.attrmap.items():
            if k in ["rdn", "id"]:
                # XXX: maybe 'login' should be editable if existent ??
                continue
            self._attrmap[k] = v
        ldapprincipal = self._get_ldap_principal()
        request = getRequest()
        # XXX: tmp - load props each time they are accessed.
        if not request or not request.get("_ldap_props_reloaded"):
            ldapprincipal.attrs.context.load()
            if request:
                request["_ldap_props_reloaded"] = 1
        for key in self._attrmap:
            self._properties[key] = ldapprincipal.attrs.get(key, "")
        UserPropertySheet.__init__(
            self, plugin.getId(), schema=None, **self._properties
        )

    def _get_ldap_principal(self):
        """returns ldap principal

        this need to be a on demand, so it does not try to persist any
        ldap-node related data in i.e. some RamCacheManager
        """
        ldap_principals = getattr(self._plugin, self._ldapprincipal_type)
        return ldap_principals[self._ldapprincipal_id]

    def canWriteProperty(self, obj, id):
        return id in self._properties

    def setProperty(self, obj, id, value):
        assert id in self._properties
        ldapprincipal = self._get_ldap_principal()
        self._properties[id] = ldapprincipal.attrs[id] = value
        try:
            ldapprincipal.context()
        except Exception as e:
            # XXX: specific exception(s)
            logger.error("LDAPUserPropertySheet.setProperty: %s" % str(e))

    def setProperties(self, obj, mapping):
        for id in mapping:
            assert id in self._properties
        ldapprincipal = self._get_ldap_principal()
        for id in mapping:
            self._properties[id] = ldapprincipal.attrs[id] = mapping[id]
        try:
            ldapprincipal.context()
        except Exception as e:
            # XXX: specific exception(s)
            logger.error("LDAPUserPropertySheet.setProperties: %s" % str(e))
