==================
Test of the plugin
==================

Setup
=====

Basics
------

.. code-block:: pycon

    >>> pas = layer['app'].acl_users
    >>> from pas.plugins.ldap.setuphandlers import _addPlugin
    >>> _addPlugin(pas)
    >>> ldap = pas['pasldap']
    >>> ldap
    <LDAPPlugin at /acl_users/pasldap>


Plugin Cache
------------

Fake a request sufficient for caching scenario:

.. code-block:: pycon

    >>> from zope.globalrequest import setRequest
    >>> setRequest(dict())

Without caching the tree is always built up fresh from the scatch:

.. code-block:: pycon

    >>> ldap.plugin_caching = False
    >>> tree = ldap._ugm()
    >>> tree is ldap._ugm()
    False

Turn on plugin cache:

.. code-block:: pycon

    >>> ldap.plugin_caching = True

The plugin cache returns the same tree (default is caching on request):

.. code-block:: pycon

    >>> tree = ldap._ugm()
    >>> tree is ldap._ugm()
    True

After invalidating the cache a new tree is returned:

.. code-block:: pycon

    >>> from pas.plugins.ldap.plugin import get_plugin_cache
    >>> cache = get_plugin_cache(ldap)
    >>> cache.invalidate()
    >>> tree is ldap._ugm
    False

    >>> from zope.globalrequest import clearRequest
    >>> clearRequest()

The volatile Plugin Cache:

.. code-block:: pycon

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

Test node.ext.ldap.cache memcached

   >>> from zope.component import queryUtility
   >>> from node.ext.ldap.interfaces import ICacheProviderFactory   
   >>> cacheFactory = queryUtility(ICacheProviderFactory)
   
Memcached is not set

.. code-block:: pycon

   >>> from bda.cache import NullCache
   >>> cache = cacheFactory()
   >>> isinstance(cache, NullCache)
   True

Turn on memcached

.. code-block:: pycon

   >>> from pas.plugins.ldap.cache import PasLdapMemcached
   >>> ldapprops = ldap._ldap_props
   >>> ldapprops.memcached = u'127.0.0.1:11211'
   
   >>> cache = cacheFactory()
   >>> cache
   <PasLdapMemcached ['127.0.0.1:11211']>

Check thread safety of memcached connection

.. code-block:: pycon

   >>> cache is cacheFactory()
   True

Change memcached config

.. code-block:: pycon

   >>> ldapprops.memcached = u'127.0.0.2:11211'
   >>> cache is cacheFactory()
   False
   
   >>> cacheFactory()
   <PasLdapMemcached ['127.0.0.2:11211']>
