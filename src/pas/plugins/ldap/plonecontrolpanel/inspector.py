"""View for inspecting LDAP directory structure and attributes for debugging."""

from node.ext.ldap import LDAPNode
from node.ext.ldap.interfaces import ILDAPGroupsConfig
from node.ext.ldap.interfaces import ILDAPProps
from node.ext.ldap.interfaces import ILDAPUsersConfig
from Products.CMFCore.interfaces import ISiteRoot
from Products.CMFPlone.utils import safe_unicode
from Products.Five import BrowserView
from zope.component import getUtility

import json


def safe_encode(val):
    """Encode a value to bytes if it's a string, otherwise return it as is."""
    if isinstance(val, str):
        return val.encode("utf-8")
    return val


class LDAPInspector(BrowserView):
    """A view to inspect the LDAP directory structure and attributes for
    debugging purposes."""

    @property
    def plugin(self):
        portal = getUtility(ISiteRoot)
        aclu = portal.acl_users
        plugin = aclu.pasldap
        return plugin

    @property
    def props(self):
        """Get the LDAP properties from the plugin."""
        return ILDAPProps(self.plugin)

    def users_children(self):
        """Get the children of the LDAP users container."""
        users = ILDAPUsersConfig(self.plugin)
        return self.children(users.baseDN)

    def groups_children(self):
        """Get the children of the LDAP groups container."""
        groups = ILDAPGroupsConfig(self.plugin)
        return self.children(groups.baseDN)

    def node_attributes(self):
        """Get the attributes of the LDAP node specified by the DN in the request."""
        dn = self.request["dn"]
        base = self.request["base"]
        if base == "users":
            users = ILDAPUsersConfig(self.plugin)
            baseDN = users.baseDN
        else:
            groups = ILDAPGroupsConfig(self.plugin)
            baseDN = groups.baseDN
        root = LDAPNode(baseDN, self.props)
        node = root.node_by_dn(safe_unicode(dn), strict=True)
        ret = dict()
        for key, val in node.attrs.items():
            try:
                if not node.attrs.is_binary(key):
                    ret[safe_unicode(key)] = safe_unicode(val)
                else:
                    ret[safe_unicode(key)] = "(Binary Data with {} Bytes)".format(
                        len(val)
                    )
            except UnicodeDecodeError:
                ret[safe_encode(key)] = "! (UnicodeDecodeError)"
            except Exception:
                ret[safe_encode(key)] = "! (Unknown Exception)"
        return json.dumps(ret)

    def children(self, baseDN):
        """Get the children of the LDAP node with the given base DN."""
        node = LDAPNode(baseDN, self.props)
        ret = list()
        # XXX: related search filters for users and groups container?
        for dn in node.search():
            ret.append({"dn": dn})
        return json.dumps(ret)
