import os
from node.ext.ldap.scope import (
    BASE,
    ONELEVEL,
    SUBTREE,
)
from node.ext.ldap.interfaces import (
    ILDAPProps,
    ILDAPUsersConfig,
    ILDAPGroupsConfig,
)
from node.ext.ldap.ugm import Ugm
from yafowil.controller import Controller
from yafowil.yaml import parse_from_YAML

class LDAPPropertiesForm(BrowserView):
    
    yaml = os.path.join(os.path.dirname(__file__), 'controlpanel.yaml')
    
    scope_vocab = [
        (str(BASE), 'BASE'),
        (str(ONELEVEL), 'ONELEVEL'),
        (str(SUBTREE), 'SUBTREE'),
    ]
    
    static_attrs = ['rdn', 'id', 'login']    

    def form(self):
        # prepare users data
        self.users_attrmap = odict()
        for key in self.static_attrs:
            self.users_attrmap[key] = self.users.attrmap.get(key)
        
        self.users_propsheet_attrmap = odict()
        for key, value in self.users.attrmap.items():
            if key in self.static_attrs:
                continue
            self.users_propsheet_attrmap[key] = value

        # prepare groups data
        self.groups_attrmap = odict()
        for key in self.static_attrs:
            self.groups_attrmap[key] = self.groups.attrmap.get(key)
        self.groups_propsheet_attrmap = odict()
        for key, value in self.groups.attrmap.items():
            if key in self.static_attrs:
                continue
            self.groups_propsheet_attrmap[key] = value

        form = parse_from_YAML(self.yaml, self,  _)
        controller = Controller(form, self.request)
        if not controller.next:
            return controller.rendered
        raise Redirect(controller.next)