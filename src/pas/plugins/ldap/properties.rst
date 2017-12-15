PropProxy
=========

.. code-block:: pycon

    >>> class SomePlugin(object):
    ...     def __init__(self):
    ...         self.settings = dict()

    >>> from pas.plugins.ldap.properties import propproxy
    >>> from pas.plugins.ldap.properties import DEFAULTS
    >>> class SomeAdapter(object):
    ...     def __init__(self, plugin):
    ...         self.plugin = plugin
    ...     someprop = propproxy('ldapprops.prop')
    >>> DEFAULTS['ldapprops.prop'] = 'default'

    >>> plugin = SomePlugin()
    >>> adapter = SomeAdapter(plugin)

    >>> adapter.someprop
    'default'

    >>> adapter.someprop = 'othervalue'
    >>> adapter.someprop
    'othervalue'


Properties
==========

.. code-block:: pycon

    >>> from pas.plugins.ldap.properties import LDAPProps
    >>> from pas.plugins.ldap.properties import UsersConfig
    >>> from pas.plugins.ldap.properties import GroupsConfig
    >>> ldapprops = LDAPProps(plugin)
    >>> usersprops = UsersConfig(plugin)
    >>> groupsprops = GroupsConfig(plugin)
