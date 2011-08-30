PropProxy
=========
::
    >>> class SomePlugin(object):
    ...     def __init__(self):
    ...         self.settings = dict()

    >>> from pas.plugins.ldap.properties import propproxy
    >>> from pas.plugins.ldap.properties import DEFAULTS
    >>> class SomeAdapter(object):
    ...     def __init__(self, plugin):
    ...         self.plugin = plugin
    ...     someprop = propproxy('ldapprops.prop')
    ...     somejson = propproxy('ldapprops.jprop', True)
    >>> DEFAULTS['ldapprops.prop'] = 'default'
    >>> DEFAULTS['ldapprops.jprop'] = '[1, 2]'

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
    