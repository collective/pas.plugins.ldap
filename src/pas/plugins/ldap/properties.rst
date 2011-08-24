PropProxy
=========
::
    >>> class SomePlugin(object):
    ...     def __init__(self):
    ...         self.ldapprops = dict()

    >>> from pas.plugins.ldap.properties import PropProxy
    >>> class SomeAdapter(object):
    ...     def __init__(self, plugin):
    ...         self.plugin = plugin
    ...     someprop = PropProxy('ldapprops', 'prop', 'default')()
    ...     somejson = PropProxy('ldapprops', 'jprop', '[1, 2]', json=True)()

    >>> plugin = SomePlugin()
    >>> adapter = SomeAdapter(plugin)

    >>> adapter.someprop 
    'default'

    >>> adapter.someprop = 'othervalue' 
    >>> adapter.someprop 
    'othervalue'
    
    >>> adapter.somejson 
    [1, 2]
    
    >>> adapter.somejson = ['foo', 'bar'] 
    >>> adapter.somejson 
    [u'foo', u'bar']
    
Properties
==========
::
    >>> from pas.plugins.ldap.properties import LDAPProps
    >>> from pas.plugins.ldap.properties import UsersConfig
    >>> from pas.plugins.ldap.properties import GroupsConfig
    >>> ldapprops = LDAPProps(plugin)
    >>> usersprops = UsersConfig(plugin)
    >>> groupsprops = GroupsConfig(plugin)
    