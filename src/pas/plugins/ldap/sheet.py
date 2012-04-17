import logging
from Acquisition import aq_base
from zope.globalrequest import getRequest
from Products.PlonePAS.interfaces.propertysheets import IMutablePropertySheet
from Products.PluggableAuthService.utils import classImplements
from Products.PluggableAuthService.UserPropertySheet import UserPropertySheet
from node.ext.ldap.interfaces import (
    ILDAPUsersConfig,
    ILDAPGroupsConfig,
)

logger = logging.getLogger('pas.plugins.ldap')

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
        self._lprincipal_id = principal.getId()
        if self._lprincipal_id in plugin.users:
            pcfg = ILDAPUsersConfig(plugin)
            self._lprincipal_type = 'users'
        else:
            pcfg = ILDAPGroupsConfig(plugin)
            self._lprincipal_type = 'groups'
        for k, v in pcfg.attrmap.items():
            if k in ['rdn', 'id']:
                # XXX: maybe 'login' should be editable if existent ??
                continue
            self._attrmap[k] = v
        lprincipal = self._get_ldap_principal()
        request = getRequest()
        # XXX: tmp - load props each time they are accessed.
        if not request or not request.get('_ldap_props_reloaded'):
            lprincipal.attrs.context.load()
            if request:
                request['_ldap_props_reloaded'] = 1
        for key in self._attrmap:
            self._properties[key] = lprincipal.attrs.get(key, '')
        UserPropertySheet.__init__(self, lprincipal, schema=None,
                                   **self._properties)

    def _get_ldap_principal(self):
        """returns ldap principal

        this need to be a on demand, so it does not try to persist any ldap-node
        related data in i.e. some RamCacheManager 
        """
        if hasattr(self, '_v_lprincipal'):
            return self._v_lprincipal
        ldap_principals = getattr(self._plugin, self._lprincipal_type)
        self._v_lprincipal = ldap_principals[self._lprincipal_id]
        return self._v_lprincipal

    def canWriteProperty(self, obj, id):
        return id in self._properties

    def setProperty(self, obj, id, value):
        assert(id in self._properties)
        lprincipal = self._get_ldap_principal()
        self._properties[id] = lprincipal.attrs[id] = value
        try:
            lprincipal.context()
        except Exception, e:
            # XXX: specific exception(s)
            logger.error('LDAPUserPropertySheet.setProperty: %s' % str(e))

    def setProperties(self, obj, mapping):
        for id in mapping:
            assert(id in self._properties)
        lprincipal = self._get_ldap_principal()
        for id in mapping:
            self._properties[id] = lprincipal.attrs[id] = mapping[id]
        try:
            lprincipal.context()
        except Exception, e:
            # XXX: specific exception(s)
            logger.error('LDAPUserPropertySheet.setProperties: %s' % str(e))

classImplements(LDAPUserPropertySheet, IMutablePropertySheet)
