# Copyright (c) 2006-2010 BlueDynamics Alliance, Austria http://bluedynamics.com
# GNU General Public License (GPL)

from StringIO import StringIO
from Products.PlonePAS.Extensions.Install import activatePluginInterfaces

from bda.pasldap._plugin import addLDAPPlugin

ID = 'ldap'
TITLE = 'LDAP Plugin'

def isNotThisProfile(context):
    return context.readDataFile("bdapasldap_marker.txt") is None

def setupPlugin(context):
    if isNotThisProfile(context):
        return 
    out = StringIO()
    portal = context.getSite()
    pas = portal.acl_users
    installed = pas.objectIds()
    if ID not in installed:
        addLDAPPlugin(pas, ID, TITLE)
        # register for various jobs
        activatePluginInterfaces(portal, ID, out)
    else:
        print >> out, TITLE+" already installed."
    print out.getvalue()
