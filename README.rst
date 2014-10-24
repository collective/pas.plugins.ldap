.. image:: https://secure.travis-ci.org/collective/pas.plugins.ldap.png
    :target: http://travis-ci.org/#!/collective/pas.plugins.ldap

This is a LDAP Plugin for the `Zope2 <http://zope2.zope.org>`_ `Pluggable Authentication Service (PAS) <http://pypi.python.org/pypi/Products.PluggableAuthService>`_.

It provides users and/or groups from an LDAP Directory.
It works in a plain Zope2 even if it depends on `PlonePAS <http://pypi.python.org/pypi/Products.PlonePAS>`_.
If `Plone <http://plone.org>`_ is installed an integration layer with a setup-profile and a plone-controlpanel page is available.

``pas.plugins.ldap`` is **not** releated to the old LDAPUserFolder/ LDAPMultiPlugins and the packages (i.e. PloneLDAP) stacked on top of it in any way.

It is based on **node.ext.ldap**, an almost framework independent ldap stack.

For now users and groups can't be added or deleted. But properties on both are read/write.
See section *TODO*.


Installation
============


Zope2
-----

Add to the instance section of your buildout::

    eggs =
        ...
        pas.plugins.ldap

    zcml =
        ...
        pas.plugins.ldap

Run buildout. Restart Zope.

Then got to your acl_users folder and add an LDAP-Plugin.
Configure it using the settings form and activate its features with the ``activate`` tab.


Plone
-----

Add to the instance section of your buildout::

    eggs =
        ...
        pas.plugins.ldap

Run buildout. Restart Plone.

Then go to the Plone control-panel, select ``extensions`` and install the LDAP Plugin.
A new LDAP Settings icon appear on the left. Click it and configure the plugin there.

To use an own integration-profile, just add to the profiles
``metadata.xml`` file::

    ...
    <dependencies>
        ...
        <dependency>profile-pas.plugins.ldap.plonecontrolpanel:default</dependency>
    </dependencies>
    ...

Additionally ldap settings can be exported and imported with ``portal_setup``.
You can place the exported ``ldapsettings.xml`` in your integration profile, so it will be imported with your next install again.
Attention: The **ldap-password is in there in plain text!**


Caching, Limitations and Future Optimizations
=============================================

By default the LDAP-queries are not cached.
A must have for a production environment is having `memcached <http://memcached.org/>`_ server configured as LDAP query cache.
Without this this module is slow (as any other module talking to LDAP will be).
Cache at least for ~6 seconds, so a page load with all its resources is covered also in worst case.

This package works fine for hundreds and also up to 3000 users (or more depending on your hardware).
But then it slows down a bit. Primary problem is here the UGM tree used.
It loads currently lots data - more than it need for a specific case - in its caching/working UGM tree.

This is not that much a problem for small amount of users.
There is room for future optimization in the underlying ``node.ext.ldap``.
Contact us if you have resources in time or budget for this development task.

The UGM tree is cached by default on the request, that means its built up every request from (cached) ldap queries.

There is an alternative adapter available which will cache the ugm tree as volatile attribute on the persistent plugin.
Volatile attributes are not persisted in the ZODB.
If the plugin object vanishes from ZODB cache the atrribute is gone.
The volatile plugin cache can be activated by loading its zcml with ``<include package="pas.plugins.ldap" file="cache_volatile.zcml"``.
The caching time can be influenced by overriding the value in ``pas.plugins.ldap.cache.VOLATILE_CACHE_MAXAGE``.
It defaults to 10 and its unit is seconds.

Please keep in mind: Caching the UGM tree longer than one request means it could contain outdated data.

If you plan a different implementation of UGM tree caching:
Just provide your own adapter implementing ``pas.plugins.ldap.interfaces.IPluginCacheHandler``.


Source Code
===========

If you want to help with the development (improvement, update, bug-fixing, ...) of ``pas.plugins.ldap`` this is a great idea!

The code is located in the `github collective <http://github.com/collective/pas.plugins.ldap>`_.

You can clone it or `get access to the github-collective <http://collective.github.com/>`_ and work directly on the project.

Maintainers are Robert Niederreiter, Jens Klein and the BlueDynamics Alliance developer team.
We appreciate any contribution and if a release is needed to be done on pypi, please just contact one of us:
`dev@bluedynamics dot com <mailto:dev@bluedynamics.com>`_


Contributors
============

- Jens W. Klein <jens@bluedynamics.com>

- Robert Niederrreiter <rnix [at] squarewave [dot] at>

- Florian Friesdorf <flo [at] chaoflow [dot] net>

- Daniel Widerin <daniel@widerin.net>
