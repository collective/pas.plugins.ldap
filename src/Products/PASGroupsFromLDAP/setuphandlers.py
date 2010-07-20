# Copyright (c) 2006-2009 BlueDynamics Alliance, Austria http://bluedynamics.com
# GNU General Public License (GPL)

from Products.PluggableAuthService.interfaces.plugins import IGroupsPlugin
from Products.PluggableAuthService.interfaces.plugins import \
    IGroupEnumerationPlugin
from Products.PluggableAuthService.interfaces.plugins import IPropertiesPlugin
from Products.PlonePAS.plugins.group import IGroupIntrospection

PLUGINID = 'groups_from_ldap'

def isNotThisProfile(context):
    return context.readDataFile("pasgroupsfromldap_marker.txt") is None

def setupPlugin(context):
    if isNotThisProfile(context):
        return 
    portal = context.getSite()
    pas = portal.acl_users
    registry = pas.plugins
    groupplugins = [id for id, pi in registry.listPlugins(IGroupsPlugin)]
    if PLUGINID not in groupplugins:
        factories = pas.manage_addProduct['PASGroupsFromLDAP']    
        factories.manage_addGroupsFromLDAPMultiPlugin(PLUGINID,
                                                      'Plone groups from LDAP',
                                                      '127.0.0.1',
                                                      '389',
                                                      'cn=admin,dc=domain,dc=com',
                                                      'secret',
                                                      'ou=groups,dc=domain,dc=com',
                                                      'SUBTREE',
                                                      'posixGroup',
                                                      'no',
                                                      'groupid',
                                                      'groupid',
                                                      'uid',
                                                      None,
                                                      REQUEST=None)
        registry.activatePlugin(IGroupsPlugin, PLUGINID )
        registry.activatePlugin(IGroupEnumerationPlugin, PLUGINID )
        registry.activatePlugin(IGroupIntrospection, PLUGINID )
        registry.activatePlugin(IPropertiesPlugin, PLUGINID )
