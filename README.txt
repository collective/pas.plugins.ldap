====================================
PAS Plugin to fetch groups from LDAP
====================================

This PAS plugin let you connect to some LDAP-Server. We've tested it with 
OpenLDAP, Apples OpenDirectory and Microsoft Active Directory.

Groups are read-only, so you cant add new groups from Plone into LDAP. This may 
be added optional in future.

You dont need any mapping like in LDAPMultiPlugins. It just take all groups from 
the DN you search in. You can use ``PASGroupsFromLDAP`` together with 
``LDAPMultiPlugins``. But ensure to disable all group related plugins of 
``LDAPMultiPlugins``.

PASGroupsFromLDAP is a multi-plugin supporting the interfaces:

* ``IGroupsPlugin`` (from ``PluggableAuthService``, short PAS)
* ``IGroupEnumerationPlugin`` (from PAS)
* ``IGroupIntrospection`` (from ``PlonePAS``)
* ``IPropertiesPlugin`` (from PAS)

Installation
============
 
Latest release or subversion needs those steps:

* make sure you have ``python-ldap`` installed, for example on Debian based OS 
  ``sudo apt-get install python-ldap`` or include it into your buildout.
* using buildout, add ``Products.PASGroupsFromLDAP`` to the eggs sections of 
  your zope instance.
* ``portal_setup`` or quickinstaller and install it.
* in ZMI ``YOURPLONE/acl_users/groups_from_ldap/manage`` you can change LDAP 
  settings
* go to the ``IPropertiesPlugin`` configuration and make sure 
  ``groups_from_ldap`` is on the top.


Update from oldschool product to egg:
=====================================

In case you need to upgrade an zope instance using an old, non-eggified version, 
of this module you need to fix your zope like so:   

* Start zope in debug mode::  
    
    >>> app['Control_Panel']['Products'].manage_delObjects(['PASGroupsFromLDAP'])
    >>> import transaction()
    >>> transaction.commit()
    
* Restart zope
* Delete PASGroupsFromLDAP plugin from you acl_users.
* Re-create the plugin.

TODO
====

* Cleanup adding / editing of the plugin.
* Do not add a default ``groups_from_ldap`` object due setuphandler

Changes
=======

* 1.2.1 (rnix - 2009-03-10)
  Fix the sometimes weird adding and edit mechanisms.
* 1.2.0 (rnix - 2009-03-10)
  Write ZMI add form for plugin. Nobody missed it yet??
* 1.1.2 (rnix - 2009-03-10)
  Document update procedure
* 1.1.1 (rnix - 2009-02-16)
  set p_changed True after managing configuration. This bug was never detected 
  since the LDAP Session itself was previously persisted in the plugin.
* 1.1 (rnix - 2009-02-10)
  Fix ldap property on plugin object due to changes in ``bda.ldap``.
* 1.1 unreleased (any)
  Initial work.

Copyright
=========

Authors: 
* Jens Klein <jens@bluedynamics.com> 
* Robert Niederreiter <robertn@bluedynamics.com> 
* Georg Gogo. Bernhard <g.bernhard@akbild.ac.at>

Copyright (C) 2007-2010 BlueDynamics Alliance, Austria

License: GNU General Public License Version 2.