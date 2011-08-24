Getter/ Setter
==============

    >>> class SomePlugin(object):
    ...     def __init__(self):
    ...         self.ldapprops = dict()

    >>> class SomeAdapter(object):
    ...     def __init__(self, plugin):
    ...         self.plugin = plugin

    >>> plugin = SomePlugin()
    >>> adapter = SomeAdapter(plugin)

    >>> from pas.plugins.ldap.properties import PropGet, PropSet
    >>> getter = PropGet('ldapprops', 'uri', 'default')
    >>> getter(adapter)
    'default'

    >>> setter = PropSet('ldapprops', 'uri')
    >>> setter(adapter, 'newvalue')
    >>> getter(adapter)
    'newvalue'

Adapter
=======

    >>> from pas.plugins.ldap.properties import LDAPProps
    >>> ldapprops = LDAPProps(plugin)
    >>> ldapprops.uri
    'newvalue'
