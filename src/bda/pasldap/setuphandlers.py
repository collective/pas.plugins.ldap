# Copyright (c) 2006-2010 BlueDynamics Alliance, Austria http://bluedynamics.com
# GNU General Public License (GPL)

from StringIO import StringIO
from Products.PlonePAS.Extensions.Install import activatePluginInterfaces

from bda.pasldap._plugin import UsersReadOnly

def isNotThisProfile(context):
    return context.readDataFile("bdapasldap_marker.txt") is None

def setupPlugin(context):
    if isNotThisProfile(context):
        return 
    out = StringIO()
    portal = context.getSite()
    pas = portal.acl_users
    installed = pas.objectIds()
    ID = 'ldap_users_readonly'
    TITLE = 'LDAP users readonly'
    if ID not in installed:
        plugin = UsersReadOnly(ID, title=TITLE)
        pas._setObject(ID, plugin)
        activatePluginInterfaces(portal, ID, out)
        #XXX move plugin to top
    else:
        print >> out, TITLE+" already installed."
    print out.getvalue()
