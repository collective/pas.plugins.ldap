from ..properties import BasePropertiesForm


class ManageLDAPPlugin(BasePropertiesForm):
    @property
    def plugin(self):
        return self.context

    def next(self, request):
        return f"{self.context.absolute_url()}/manage_ldapplugin"
