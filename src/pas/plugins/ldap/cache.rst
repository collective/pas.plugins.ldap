==================
Test of the plugin
==================

Setup
=====

Basics
------

::
    >>> pas = layer['app'].acl_users
    >>> from pas.plugins.ldap.setuphandlers import _addPlugin
    >>> _addPlugin(pas)
    >>> ldap = pas['pasldap']
    >>> ldap
    <LDAPPlugin at /acl_users/pasldap>


Plugin Cache
------------

Fake a request sufficient for caching scenario::
    >>> from zope.globalrequest import setRequest
    >>> setRequest(dict())

Without caching the tree is always built up fresh from the scatch::

    >>> ldap.plugin_caching = False
    >>> tree = ldap._ugm()
    >>> tree is ldap._ugm()
    False

Turn on plugin cache

    >>> ldap.plugin_caching = True

The plugin cache returns the same tree (default is caching on request)::

    >>> tree = ldap._ugm()
    >>> tree is ldap._ugm()
    True

After invalidating the cache a new tree is returned::

    >>> from pas.plugins.ldap.plugin import get_plugin_cache
    >>> cache = get_plugin_cache(ldap)
    >>> cache.invalidate()
    >>> tree is ldap._ugm
    False

    >>> from zope.globalrequest import clearRequest
    >>> clearRequest()

The volatile Plugin Cache::

    >>> from zope.component import provideAdapter
    >>> from pas.plugins.ldap.cache import VolatilePluginCache
    >>> provideAdapter(VolatilePluginCache)
    >>> cache = get_plugin_cache(ldap)
    >>> isinstance(cache, VolatilePluginCache)
    True

    >>> tree = ldap._ugm()
    >>> tree is ldap._ugm()
    True

    >>> cache.invalidate()
    >>> tree is ldap._ugm()
    False
