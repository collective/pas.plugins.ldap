import logging
from Products.PlonePAS.interfaces.propertysheets import IMutablePropertySheet
from Products.PluggableAuthService.utils import classImplements
from Products.PluggableAuthService.UserPropertySheet import UserPropertySheet
from node.ext.ldap.interfaces import ILDAPUsersConfig

logger = logging.getLogger('bda.plone.ldap')

class LDAPUserPropertySheet(UserPropertySheet):

    def __init__(self, user, plugin):
        """Instanciate LDAPUserPropertySheet.

        @param user: user id
        @param plugin: LDAPPlugin instance
        """
        self._plugin = plugin
        self._properties = dict()
        self._luser = plugin.users[user.getId()]
        self._ucfg = ILDAPUsersConfig(plugin)
        self._attrmap = dict()
        for k, v in self._ucfg.attrmap.items():
            if k in ['rdn', 'id']:
                # XXX: maybe 'login' should be editable if existent ??
                continue
            self._attrmap[k] = v

        # XXX: tmp - load props each time they are accessed.
        if not self._plugin.REQUEST.get('_ldap_props_reloaded'):
            self._luser.attrs.context.load()
            self._plugin.REQUEST['_ldap_props_reloaded'] = 1

        for key in self._attrmap:
            self._properties[key] = self._luser.attrs.get(key, '')
        UserPropertySheet.__init__(self, user, schema=None, **self._properties)

    def canWriteProperty(self, obj, id):
        return id in self._properties

    def setProperty(self, obj, id, value):
        assert(id in self._properties)
        self._properties[id] = self._luser.attrs[id] = value
        try:
            self._luser.context()
        except Exception, e:
            # XXX: specific exception(s)
            logger.error('LDAPUserPropertySheet.setProperty: %s' % str(e))

    def setProperties(self, obj, mapping):
        for id in mapping:
            assert(id in self._properties)
        for id in mapping:
            self._properties[id] = self._luser.attrs[id] = mapping[id]
        try:
            self._luser.context()
        except Exception, e:
            # XXX: specific exception(s)
            logger.error('LDAPUserPropertySheet.setProperties: %s' % str(e))

classImplements(LDAPUserPropertySheet, IMutablePropertySheet)
