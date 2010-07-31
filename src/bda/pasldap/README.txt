=================
PASGroupsFromLDAP 
=================

-------
Purpose
-------
This PAS plugin let you connect to some LDAP-Server. We've tested it with 
OpenLDAP, Apples OpenDirectory and Microsoft Active Directory.

Groups are read-only, so you cant add new groups from Plone into LDAP. This 
may be added optional in future.

You dont need any mapping like in LDAPMultiPlugins. It just take all groups 
from the DN you search in. We're using PASGroupsFromLDAP together with 
LDAPMultiPlugins. But we disabled all group related plugins of LDAPMultiPlugins.

PASGroupsFromLDAP is a multi-plugin supporting the interfaces:

 * IGroupsPlugin (from PluggableAuthService, short PAS)

 * IGroupEnumerationPlugin (from PAS)

 * IGroupIntrospection (from PlonePAS)

 * IPropertiesPlugin (from PAS)


Installation
 
 Latest release or subversion needs those steps:

 * make sure you have python-ldap installed, for example 
   'sudo apt-get install python-ldap'

 * fetch the generic python module 'bda.ldap' from 
   "SVN":http://svn.plone.org/svn/collective/bda.ldap/trunk/

 * install it: 'sudo python setup.py install'
 
 * or get it from the cheeseshop: 'easy_install bda.ldap'
 
 * fetch the Product 'PASGroupsFromLDAP' from 
   "SVN":http://svn.plone.org/svn/collective/PASGroupsFromLDAP/trunk/ or
   take the latest release.

 * copy it into your Products folder.

 * use quickinstaller and install it.

 * in ZMI YOURPLONE/acl_users/groups_from_ldap/manage you can make your LDAP 
   settings

 * go to the IPropertiesPlugin configuration and make sure groups_from_ldap 
   is on the top.


TODO:

 * refine connection checker, it just check if bind works, nothing else.

 * find out if the query-string escaping feature needed for AD can be enabled 
   for OpenLDAP et al too.

 * set groups_from_ldap in IPropertiesPlugin at top.

 * add a ZMI-add form; at the moment you need to quickinstall it or use 
   generic setup to get the plugin into your acl_users.
 
Copyright

 Author: Jens Klein "jens@bluedynamics.com":mailto:jens@bluedynamics.com, 
         Robert Niederreiter "robertn@bluedynamics.com":mailto:robertn@bluedynamics.com, 
         Georg Gogo. Bernhard "g.bernhard@akbild.ac.at":mailto:g.bernhard@akbild.ac.at

 Copyright (C) 2007 BlueDynamics Alliance, Klein & Partner KEG, Innsbruck, Austria

 License: GNU General Public License Version 2 or later 
