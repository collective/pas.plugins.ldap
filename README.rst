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
        
Run buildout. Restart Zope.

Then got to your acl_users folder and add an LDAP-Plugin. Configure it using the
settings form and activate its features with the ``activate`` tab.


Plone
-----

Add to the instance section of your buildout::

    eggs = 
        ...
        pas.plugins.ldap

Run buildout. Restart Plone.

Then go to the Plone control-panel, select ``extensions`` and install the LDAP
Plugin. A new LDAP Settings icon appear on the left. Click it and configure the
plugin there.

To use an own integration-profile, just add to the profiles
``metadata.xml`` file::

    ...
    <dependencies>
        ...
        <dependency>profile-pas.plugins.ldap.plonecontrolpanel:default</dependency>
    </dependencies>
    ...

Additionally ldap settings can be exported and imported with ``portal_setup``.
You can place the exported ``ldapsettings.xml`` in your integration profile, so
it will be imported with your next install again. Attention: The **ldap-password
is in there in plain text!**


Source Code
===========

If you want to help with the development (improvement, update, bug-fixing, ...)
of ``pas.plugins.ldap`` this is a great idea!

The code is located in the
`github collective <http://github.com/bluedynamics/pas.plugins.ldap>`_.

You can clone it or `get access to the github-collective
<http://collective.github.com/>`_ and work directly on the project.

Maintainers are Robert Niederreiter, Jens Klein and the BlueDynamics Alliance
developer team. We appreciate any contribution and if a release is needed
to be done on pypi, please just contact one of us
`dev@bluedynamics dot com <mailto:dev@bluedynamics.com>`_


Contributors
============

- Jens W. Klein <jens [at] bluedynamics [dot] com>

- Robert Niederrreiter <rnix [at] squarewave [dot] at>

- Florian Friesdorf <flo [at] chaoflow [dot] net>
