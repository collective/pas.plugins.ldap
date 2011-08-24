from zope.interface import implements
from zope.component import adapts
from node.ext.ldap.interfaces import (
    ILDAPProps,
    ILDAPUsersConfig,
    ILDAPGroupsConfig,
)
from .interfaces import ILDAPPlugin

class PropGet(object):
    
    def __init__(self, proptype, key, default=None):
        self.proptype = proptype
        self.key = key
        self.default = default
        
    def __call__(self, context):
        props = getattr(context.plugin, self.proptype)
        return props.get(self.key, self.default)

class PropSet(object):
    
    def __init__(self, proptype, key):
        self.proptype = proptype
        self.key = key
        
    def __call__(self, context, value):
        props = getattr(context.plugin, self.proptype)
        props[self.key] = value
    
TLDAP = 'ldapprops'

class LDAPProps(object):

    implements(ILDAPProps)
    adapts(ILDAPPlugin)
    
    def __init__(self, plugin):
        self.plugin = plugin

    uri = property(
        PropGet(TLDAP, 'uri', ''), 
        PropSet(TLDAP, 'uri'))    
    
    user = property(
        PropGet(TLDAP, 'user', ''), 
        PropSet(TLDAP, 'user'))