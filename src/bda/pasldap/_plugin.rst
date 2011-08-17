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

    >>> [_['id'] for _ in ldap.enumerateGroups(id='group*', sort_by='id')]
    ['group0', 'group1', 'group2', 'group3', 'group4', 'group5', 'group6', 
    'group7', 'group8', 'group9']

    >>> ldap.enumerateGroups(id='group*', exact_match=True)
    ()

    >>> ldap.enumerateGroups(id='group5', exact_match=True)
    [{'pluginid': 'ldap_bda', 'id': 'group5'}]

    >>> len(ldap.enumerateGroups(id='group*', max_results=3))
    3
    
    
IGroupsPlugin
-------------

::

    >>> user = pas.getUserById('uid9')
    >>> ldap.getGroupsForPrincipal(user)
    [u'group9']

    >>> user = pas.getUserById('uid1')
    >>> ldap.getGroupsForPrincipal(user)
    [u'group1', u'group2', u'group3', u'group4', u'group5', 
    u'group6', u'group7', u'group8', u'group9']

    >>> user = pas.getUserById('uid0')
    >>> ldap.getGroupsForPrincipal(user)
    []

IPropertiesPlugin
-----------------

see PlonePAS, IMutablePropertiesPlugin

IUserEnumerationPlugin
----------------------

Signature is ``enumerateUsers( id=None, login=None, exact_match=False,
sort_by=None, max_results=None, **kw)``

::

    >>> ldap.enumerateUsers(id='uid1')
    [{'pluginid': 'ldap_bda', 'login': u'cn1', 'id': 'uid1'}]

    >>> ldap.enumerateUsers(id='uid*')
        [{'pluginid': 'ldap_bda', 'login': u'cn0', 'id': 'uid0'}, 
        {'pluginid': 'ldap_bda', 'login': u'cn1', 'id': 'uid1'}, 
        {'pluginid': 'ldap_bda', 'login': u'cn2', 'id': 'uid2'}, 
        {'pluginid': 'ldap_bda', 'login': u'cn3', 'id': 'uid3'}, 
        {'pluginid': 'ldap_bda', 'login': u'cn4', 'id': 'uid4'}, 
        {'pluginid': 'ldap_bda', 'login': u'cn5', 'id': 'uid5'}, 
        {'pluginid': 'ldap_bda', 'login': u'cn6', 'id': 'uid6'}, 
        {'pluginid': 'ldap_bda', 'login': u'cn7', 'id': 'uid7'}, 
        {'pluginid': 'ldap_bda', 'login': u'cn8', 'id': 'uid8'}, 
        {'pluginid': 'ldap_bda', 'login': u'cn9', 'id': 'uid9'}]
        
    >>> [_['id'] for _ in ldap.enumerateUsers(id='uid*', sort_by='id')]
    ['uid0', 'uid1', 'uid2', 'uid3', 'uid4', 'uid5', 'uid6', 'uid7', 'uid8', 
    'uid9']
        
    >>> ldap.enumerateUsers(id='uid*', exact_match=True)
    ()

    >>> ldap.enumerateUsers(id='uid4', exact_match=True)
    [{'pluginid': 'ldap_bda', 'login': u'cn4', 'id': 'uid4'}]

    >>> len(ldap.enumerateUsers(id='uid*', max_results=3))
    3
    
    
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
