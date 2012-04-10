import logging
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
        self._plugin = plugin
        self._properties = dict()
        if principal.getId() in plugin.users:
            self._pcfg = ILDAPUsersConfig(plugin)
            self._lprincipal = plugin.users[principal.getId()]
        else:
            self._pcfg = ILDAPGroupsConfig(plugin)
            self._lprincipal = plugin.groups[principal.getId()]
        
        self._attrmap = dict()
        for k, v in self._pcfg.attrmap.items():
            if k in ['rdn', 'id']:
                # XXX: maybe 'login' should be editable if existent ??
                continue
            self._attrmap[k] = v

        # XXX: tmp - load props each time they are accessed.
        # XXX 2: when called from a service such as zc.async,
        # the plugin might not have a REQUEST. Check for its existence first!
        request = getattr(self._plugin, 'REQUEST', None)
        if not request or not self._plugin.REQUEST.get('_ldap_props_reloaded'):
            self._lprincipal.attrs.context.load()
            if request:
                self._plugin.REQUEST['_ldap_props_reloaded'] = 1
        for key in self._attrmap:
            self._properties[key] = self._lprincipal.attrs.get(key, '')
        UserPropertySheet.__init__(self, principal, schema=None, 
                                   **self._properties)

    def canWriteProperty(self, obj, id):
        return id in self._properties

    def setProperty(self, obj, id, value):
        assert(id in self._properties)
        self._properties[id] = self._lprincipal.attrs[id] = value
        try:
            self._lprincipal.context()
        except Exception, e:
            # XXX: specific exception(s)
            logger.error('LDAPUserPropertySheet.setProperty: %s' % str(e))

    def setProperties(self, obj, mapping):
        for id in mapping:
            assert(id in self._properties)
        for id in mapping:
            self._properties[id] = self._lprincipal.attrs[id] = mapping[id]
        try:
            self._lprincipal.context()
        except Exception, e:
            # XXX: specific exception(s)
            logger.error('LDAPUserPropertySheet.setProperties: %s' % str(e))

classImplements(LDAPUserPropertySheet, IMutablePropertySheet)
