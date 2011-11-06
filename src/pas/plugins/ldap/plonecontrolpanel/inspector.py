# -*- coding: utf-8 -*-
import json
import types
from node.ext.ldap import LDAPNode
from node.ext.ldap.interfaces import (
    ILDAPProps,
    ILDAPUsersConfig,
    ILDAPGroupsConfig,
)
from zope.component import getUtility
from Products.Five import BrowserView
from Products.CMFCore.interfaces import ISiteRoot


class LDAPInspector(BrowserView):
    
    @property
    def plugin(self):
        portal = getUtility(ISiteRoot)
        aclu = portal.acl_users
        plugin = aclu.pasldap
        return plugin
    
    @property
    def props(self):
        return ILDAPProps(self.plugin)
    
    def users_children(self):
        users = ILDAPUsersConfig(self.plugin)
        return self.children(users.baseDN)
    
    def groups_children(self):
        groups = ILDAPGroupsConfig(self.plugin)
        return self.children(groups.baseDN)
    
    def node_attributes(self):
        rdn = self.request['rdn']
        base = self.request['base']
        if base == 'users':
            users = ILDAPUsersConfig(self.plugin)
            baseDN = users.baseDN
        else:
            groups = ILDAPGroupsConfig(self.plugin)
            baseDN = groups.baseDN
        root = LDAPNode(baseDN, self.props)
        node = root[rdn]
        ret = dict()
        for key in node.attrs:
            try:
                val = node.attrs[key]
                if type(val) is types.ListType:
                    val = [v.encode('utf-8') for v in val]
                else:
                    val = val.encode('utf-8')
                ret[key.encode('utf-8')] = val
            except UnicodeDecodeError:
                ret[key.encode('utf-8')] = 'Unknown Data'
        return json.dumps(ret)
    
    def children(self, baseDN):
        node = LDAPNode(baseDN, self.props)
        ret = list()
        for key in node:
            ret.append({'rdn': key})
        return json.dumps(ret)