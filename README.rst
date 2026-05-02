
.. image:: https://img.shields.io/pypi/v/pas.plugins.ldap.svg
    :target: https://pypi.python.org/pypi/pas.plugins.ldap
    :alt: Latest PyPI version

.. image:: https://img.shields.io/pypi/dm/pas.plugins.ldap.svg
    :target: https://pypi.python.org/pypi/pas.plugins.ldap
    :alt: Number of PyPI downloads

.. image:: https://github.com/collective/pas.plugins.ldap/actions/workflows/tests.yaml/badge.svg
    :target: https://github.com/collective/pas.plugins.ldap/actions/workflows/tests.yaml
    :alt: Test the pas.plugins.ldap code

.. image:: https://coveralls.io/repos/collective/pas.plugins.ldap/badge.svg?branch=master&service=github
    :target: https://coveralls.io/github/collective/pas.plugins.ldap?branch=master

This is a `LDAP <https://en.wikipedia.org/wiki/Lightweight_Directory_Access_Protocol>`_ Plugin for the `Zope <https://www.zope.dev/>`_ `Pluggable Authentication Service (PAS) <https://pypi.org/project/Products.PluggableAuthService/>`_.

It provides users and/or groups from an LDAP directory.

It works in a plain Zope even if it depends on `PlonePAS <https://pypi.org/project/Products.PlonePAS>`_.

If `Plone <https://plone.org>`_ is installed an integration layer with a setup-profile and a plone-controlpanel page is available.

``pas.plugins.ldap`` is **not** releated to the old `LDAPUserFolder <https://pypi.org/project/Products.LDAPUserFolder/>`_ / `LDAPMultiPlugins <https://pypi.org/project/Products.LDAPMultiPlugins/>`_ and the packages (i.e. `PloneLDAP <https://pypi.org/project/Products.PloneLDAP/>`_) stacked on top of it in any way.

It is based on `node.ext.ldap <https://pypi.org/project/node.ext.ldap/>`_, an almost framework independent LDAP stack.

For now users and groups can't be added or deleted. Properties on both are read/write.

See section *TODO*.


Installation
============

Dependencies
------------

This package depends on ``python-ldap``.

To build it correctly you need to have some development libraries included in your system.

On a Debian-based installation use:

.. code-block:: console

    sudo apt install python-dev libldap2-dev libsasl2-dev libssl-dev


Zope
----

Add to the instance section of your buildout:

.. code-block:: ini

    eggs =
        ...
        pas.plugins.ldap

    zcml =
        ...
        pas.plugins.ldap

Run ``buildout``. Restart Zope.

Browse to your ``acl_users`` folder and add an ``LDAP-Plugin``.

Configure it using the settings form and activate its features with the ``activate`` tab.

----

Plone
-----

Add to the instance section of your ``buildout``:

.. code-block:: ini

    eggs =
        ...
        pas.plugins.ldap

Run ``buildout``. Restart Plone.

Then go to the Plone control-panel, select ``Addons`` and install the ``LDAP / Active Directory Support``.

So, you can navigate to ``Site Setup`` > ``Users`` > ``LDAP / AD Support`` and click it and configure the plugin there.

To use an own integration-profile, add to the profiles ``metadata.xml`` file:

.. code-block:: xml

    ...
    <dependencies>
        ...
        <dependency>profile-pas.plugins.ldap.plonecontrolpanel:default</dependency>
    </dependencies>
    ...

Additionally ldap settings can be exported and imported with ``portal_setup``.
You can place the exported ``ldapsettings.xml`` file in your integration profile, so it will be imported with your next install again.

**Warning:**

**The LDAP-password is stored in there in plain text!**

But anonymous bindings are possible.


Logging
-------

To get detailed output of all LDAP-operations and much more set the logging level to debug.
Attention, this is lots of output.

LDAP as an external service might be down, non-responsive or slow.
This package logs such events to raise awareness.
There are two environment variables to control the logging of LDAP-errors:

``PAS_PLUGINS_LDAP_ERROR_LOG_TIMEOUT``
    First LDAP-error is logged, further errors ignored until the given number of seconds have passed.
    This supresses flooding logs if LDAP is down.
    Default: 300.0 (time in seconds, float).

``PAS_PLUGINS_LDAP_LONG_RUNNING_LOG_THRESHOLD``
    Log long running LDAP/PAS operations.
    If a PAS operation takes longer than he given number of seconds, log it as error.
    Default: 5 (time in seconds, float).


Timeouts
--------

Global LDAP timeouts are set and controlled by two environment variables:

``PAS_PLUGINS_LDAP_OPT_NETWORK_TIMEOUT``
    Connection timeout.
    Default: 1.0s

``PAS_PLUGINS_LDAP_OPT_TIMEOUT``
    Overall timeout.
    Default: 30.0s

See details in python-ldap documentation: OPT_NETWORK_TIMEOUT and OPT_TIMEOUT.


Caching
-------

**Without caching this module is slow** (as any other module talking to LDAP will be).

By **default** the LDAP-queries are **not cached**.

A **must have** for a production environment is having `memcached <https://memcached.org/>`_ server configured as LDAP query cache.

Cache at least for ~6 seconds, so a page load with all its resources is covered also in worst case.

The UGM tree is cached by default on the request, that means its built up every request from (cached) ldap queries.

There is an alternative adapter available which will cache the ugm tree as volatile attribute (``_v_...``) on the persistent plugin.

Volatile attributes are not persisted in the ZODB.
If the plugin object vanishes from ZODB cache the atrribute is gone.

The volatile plugin cache can be activated by loading its zcml with ``<include package="pas.plugins.ldap" file="cache_volatile.zcml"``.

The caching time can be influenced by overriding the value in ``pas.plugins.ldap.cache.VOLATILE_CACHE_MAXAGE``.

It defaults to 10 and its unit is seconds.

**Note:**

**Caching the UGM tree longer than one request means it could contain outdated data.**

If you plan a different implementation of UGM tree caching,provide your own adapter implementing ``pas.plugins.ldap.interfaces.IPluginCacheHandler``.


Limitations and Future Optimizations
====================================

This package was not tested/developed with Windows.
It may work under Windows if ``python-ldap`` is installed properly and recognized by buildout.

This package works fine for several 10000 users or groups, **unless you list users**.

This is not that much a problem for small amount of users.
There is room for future optimization in the underlying `node.ext.ldap <https://pypi.org/project/node.ext.ldap/>`_.


Source Code
===========

If you want to help with the development (improvement, update, bug-fixing, ...) of ``pas.plugins.ldap`` this is a great idea!

The code is located in the `GitHub Collective <https://github.com/collective/pas.plugins.ldap>`_.

You can clone it or `get access to the GitHub Collective <https://collective.github.io/>`_ and work directly on the project.

Maintainers are Robert Niederreiter, Jens Klein and the `BlueDynamics Alliance <https://bluedynamics.com/>`_ developer team.

We appreciate any contribution and if a release is needed to be done on pypi, please just contact one of us:
`dev@bluedynamics dot com <mailto:dev@bluedynamics.com>`_


Contributors
============

- Jens W. Klein
- Robert Niederrreiter
- Florian Friesdorf
- Daniel Widerin
- Johannes Raggam
- Luca Fabbri
- Leonardo J. Caballero G.


License
=======

The project is licensed under the GPLv2.
