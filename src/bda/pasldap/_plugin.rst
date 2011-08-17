==================
Test of the plugin
==================

Setup
=====

Basics
------

::
    >>> app = layer['app']
    >>> z2.login(app.acl_users, 'admin')
  
Turn into a PAS user folder::

    >>> from Products.PlonePAS.Extensions.Install import migrate_root_uf
    >>> migrate_root_uf(app)
    >>> pas = app.acl_users
    >>> pas
    <PluggableAuthService at /acl_users>
    
Create
------

::
    >>> from bda.pasldap.setuphandlers import _addPlugin
    >>> _addPlugin(app.acl_users)
    >>> sorted(pas.objectIds())
    ['chooser', 'credentials_basic_auth', 'credentials_cookie_auth', 'ldap_bda', 
    'plugins', 'roles', 'sniffer', 'users']
    
    >>> ldap = pas['ldap_bda']
    
PAS Plugins
===========

IAuthenticationPlugin
---------------------

::

    >>> ldap.authenticateCredentials({'login':'cn0', 'password': 'secret0'})
    (u'uid0', 'cn0')

    >>> ldap.authenticateCredentials({'login':'admin', 'password': 'admin'})
    
    >>> ldap.authenticateCredentials({'login':'nonexist', 'password': 'dummy'})
    

IGroupEnumerationPlugin
-----------------------

Signature is ``enumerateGroups(self, id=None, exact_match=False, sort_by=None,
max_results=None, **kw)``

::

    >>> ldap.enumerateGroups(id='group2')
    [{'pluginid': 'ldap_bda', 'id': 'group2'}]

    >>> print sorted([_['id'] for _ in ldap.enumerateGroups(id='group*')])
    ['group0', 'group1', 'group2', 'group3', 'group4', 'group5', 'group6', 
    'group7', 'group8', 'group9']


IGroupsPlugin
-------------

IPropertiesPlugin
-----------------

IUserEnumerationPlugin
----------------------

IDeleteCapability
-----------------

PlonePAS
========

IGroupCapability
----------------

IPasswordSetCapability
----------------------

IGroupManagement
----------------

IMutablePropertiesPlugin
------------------------

IUserManagement
---------------
