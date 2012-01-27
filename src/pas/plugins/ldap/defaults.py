from node.ext.ldap.scope import ONELEVEL

DEFAULTS = {
    'server.uri'              : 'ldap://127.0.0.1:12345',
    'server.user'             : 'cn=Manager,dc=my-domain,dc=com',
    'server.password'         : 'secret',
    'server.escape_queries'   : False,
    'server.start_tls'        : False,

    'cache.cache'             : False,
    'cache.memcached'         : '127.0.0.1:11211',
    'cache.timeout'           : 300, # seconds

    'users.baseDN'            : 'ou=users,dc=my-domain,dc=com',
    'users.attrmap'           : {"rdn": "uid", 
                                 "id": "uid", 
                                 "login": "uid",
                                 "fullname": "cn", 
                                 "email": "mail",
                                 'location': 'l'},
    'users.scope'             : ONELEVEL,
    'users.queryFilter'       : '(objectClass=inetOrgPerson)',
    'users.objectClasses'     : ["inetOrgPerson"],
    'users.memberOfSupport'   : False,

    'groups.baseDN'           : 'ou=groups,dc=my-domain,dc=com',
    'groups.attrmap'          : {"rdn": "cn", 
                                 "id": "cn", 
                                 "title": "o",
                                 "description": "description"},
    'groups.scope'            : ONELEVEL,
    'groups.queryFilter'      : '(objectClass=groupOfUniqueNames)',
    'groups.objectClasses'    : ["groupOfUniqueNames"],
    'groups.memberOfSupport'  : False,

    'roles.baseDN'           : 'ou=roles,dc=my-domain,dc=com',
    'roles.attrmap'          : {"rdn": "cn", 
                                 "id": "cn", 
                                 "title": "o",
                                 "description": "description"},
    'roles.scope'            : ONELEVEL,
    'roles.queryFilter'      : '(objectClass=groupOfUniqueNames)',
    'roles.objectClasses'    : ["groupOfUniqueNames"],
    'roles.memberOfSupport'  : False,



}