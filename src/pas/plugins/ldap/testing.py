from node.ext.ldap import testing as ldaptesting
from node.ext.ldap.interfaces import ICacheProviderFactory
from node.ext.ldap.interfaces import ILDAPGroupsConfig
from node.ext.ldap.interfaces import ILDAPProps
from node.ext.ldap.interfaces import ILDAPUsersConfig
from .cache import cacheProviderFactory
from .interfaces import ICacheSettingsRecordProvider
from .plonecontrolpanel.cache import CacheSettingsRecordProvider
from .properties import LDAPProps
from plone.registry import Registry
from plone.registry.interfaces import IRegistry
from plone.testing import Layer
from plone.testing import z2
from Products.CMFCore.interfaces import ISiteRoot
from zope.component import adapter
from zope.component import provideAdapter
from zope.component import provideUtility
from zope.interface import implementer
from zope.interface import Interface
from Products.PlonePAS.setuphandlers import migrate_root_uf
from Products.PlonePAS.setuphandlers import registerPluginTypes
from zope.configuration import xmlconfig
from zope.dottedname.resolve import resolve

SITE_OWNER_NAME = SITE_OWNER_PASSWORD = "admin"


@implementer(ILDAPProps)
@adapter(Interface)
def ldapprops(context):
    props = LDAPProps(context)

    props.uri = ldaptesting.props.uri
    props.user = ldaptesting.props.user
    props.password = ldaptesting.props.password
    props.cache = ldaptesting.props.cache
    props.page_size = ldaptesting.props.page_size

    return props


@implementer(ILDAPUsersConfig)
@adapter(Interface)
def usersconfig(context):
    return ldaptesting.LDIF_groupOfNames_10_10.ucfg


@implementer(ILDAPGroupsConfig)
@adapter(Interface)
def groupsconfig(context):
    return ldaptesting.LDIF_groupOfNames_10_10.gcfg


class PASLDAPLayer(Layer):

    defaultBases = (ldaptesting.LDIF_groupOfNames_10_10, z2.INTEGRATION_TESTING)

    # Products that will be installed, plus options
    products = (
        ("Products.GenericSetup", {"loadZCML": True}),  # noqa
        ("Products.CMFCore", {"loadZCML": True}),  # noqa
        ("Products.PluggableAuthService", {"loadZCML": True}),  # noqa
        ("Products.PluginRegistry", {"loadZCML": True}),  # noqa
        ("Products.PlonePAS", {"loadZCML": True}),  # noqa
    )

    def setUp(self):
        self.setUpZCML()

    def testSetUp(self):
        self.setUpProducts()
        provideUtility(self["app"], provides=ISiteRoot)
        provideUtility(self["app"], provides=ISiteRoot)

        # Layer is not a plone site, registry of some utilities is required
        provideUtility(Registry(), provides=IRegistry)
        provideUtility(cacheProviderFactory(), provides=ICacheProviderFactory)
        provideUtility(
            CacheSettingsRecordProvider(), provides=ICacheSettingsRecordProvider
        )
        migrate_root_uf(self["app"])
        registerPluginTypes(self["app"].acl_users)

    def setUpZCML(self):
        """Stack a new global registry and load ZCML configuration of Plone
        and the core set of add-on products into it.
        """

        # Load dependent products's ZCML
        def loadAll(filename):
            for p, config in self.products:
                if not config["loadZCML"]:
                    continue
                package = resolve(p)
                try:
                    xmlconfig.file(
                        filename, package, context=self["configurationContext"]
                    )
                except OSError:
                    pass

        loadAll("meta.zcml")
        loadAll("configure.zcml")
        loadAll("overrides.zcml")
        provideAdapter(ldapprops)
        provideAdapter(usersconfig)
        provideAdapter(groupsconfig)

    def setUpProducts(self):
        """Install all old-style products listed in the the ``products`` tuple
        of this class.
        """
        for prd, config in self.products:
            z2.installProduct(self["app"], prd)


PASLDAP_FIXTURE = PASLDAPLayer()
