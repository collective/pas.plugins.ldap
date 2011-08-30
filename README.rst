This is a LDAP Plugin for the `Zope2 <http://zope2.zope.org>`_
`Pluggable Authentication Service (PAS) <http://pypi.python.org/pypi/Products.PluggableAuthService>`_.

It provides users and/or groups from an LDAP Directory. It works in a plain
Zope2 even if it depends on
`PlonePAS <http://pypi.python.org/pypi/Products.PlonePAS>`_.
If `Plone <http://plone.org>`_ is installed an
integration layer with a setup-profile and a plone-controlpanel page is
available.

``pas.plugins.ldap`` is **not** releated to the old LDAPUserFolder/
LDAPMultiPlugins and the packages stacked on top of it in any way.

It is based on **node.ext.ldap**, an almost framework independent ldap stack.

For now users and groups can't be added or deleted. But properties on both are
read/write. See section *TODO*.

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
        
Let buildout run. Restart Zope.

Then got to your acl_users folder and add an LDAP-Plugin. Configure it using the
settings form and activate its features with the ``activate`` tab.

Plone
-----

Add to the instance section of your buildout::

    eggs = 
        ...
        pas.plugins.ldap

Let buildout run. Restart Plone.

The go to the Plone control-panel, select ``extensions`` and install the LDAP
Plugin. A new LDAP Settings icon appear on the left. Click it and configure the
plugin there.

Source Code
===========

The sources are in a GIT DVCS with its main branches at
`github <http://github.com/bluedynamics/pas.plugins.ldap>`_.

We'd be happy to see many forks and pull-requests to make pas.plugins.ldap even
better.

Contributors
============

- Jens W. Klein <jens@bluedynamics.com>

- Robert Niederrreiter <rnix@squarewave.at>

- Florian Friesdorf <flo@chaoflow.net>
