import copy
import json
from zope.interface import implements
from zope.component import adapts
from node.ext.ldap.interfaces import (
    ILDAPProps,
    ILDAPUsersConfig,
    ILDAPGroupsConfig,
)
from .interfaces import ILDAPPlugin

class PropProxy(object):
    
    def __init__(self, proptype, key, default=None, json=False):
        self.proptype = proptype
        self.key = key
        self.default = copy.copy(default)
        self.json = json
                    
    def __call__(self):
        def _getter(context):
            props = getattr(context.plugin, self.proptype)
            value = props.get(self.key, self.default)
            if self.json:
                return json.loads(value)
            return value
        def _setter(context, value):
            if self.json:
                value = json.dumps(value)
            props = getattr(context.plugin, self.proptype)
            props[self.key] = value
        return property(_getter, _setter)


TLDAP = 'ldapprops'
TUSERS = 'usersconfig'
TGROUPS = 'groupsconfig'


class LDAPProps(object):

    implements(ILDAPProps)
    adapts(ILDAPPlugin)
    
    def __init__(self, plugin):
        self.plugin = plugin

    uri = PropProxy(TLDAP, 'uri', '')()
    user = PropProxy(TLDAP, 'user', '')()
    password = PropProxy(TLDAP, 'password', '')()
    

class UsersConfig(object):

    implements(ILDAPUsersConfig)
    adapts(ILDAPPlugin)
    
    def __init__(self, plugin):
        self.plugin = plugin

    baseDN = PropProxy(TUSERS, 'baseDN', '')()
    attrmap = PropProxy(TUSERS, 'attrmap', '{}', json=True)()
    scope = PropProxy(TUSERS, 'scope', '')()
    queryFilter = PropProxy(TUSERS, 'queryFilter', '')()
    objectClasses = PropProxy(TUSERS, 'objectClasses', '()', json=True)()

    
class GroupsConfig(object):

    implements(ILDAPGroupsConfig)
    adapts(ILDAPPlugin)
    
    def __init__(self, plugin):
        self.plugin = plugin

    baseDN = PropProxy(TUSERS, 'baseDN', '')()
    attrmap = PropProxy(TUSERS, 'attrmap', '{}', json=True)()
    scope = PropProxy(TUSERS, 'scope', '')()
    queryFilter = PropProxy(TUSERS, 'queryFilter', '')()
    objectClasses = PropProxy(TUSERS, 'objectClasses', '()', json=True)()
        