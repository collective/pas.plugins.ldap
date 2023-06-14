from ..properties import BasePropertiesForm


class ManageLDAPPlugin(BasePropertiesForm):
    @property
    def plugin(self):
        return self.context

    def next(self, request):
        return "%s/manage_ldapplugin" % self.context.absolute_url()
