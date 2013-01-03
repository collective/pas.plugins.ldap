from zope.interface import (
    Interface,
    implementer,
)
from zope.component import (
    adapter,
    provideAdapter,
    provideUtility,
)
from plone.testing import (
    Layer,
    zodb,
    zca,
    z2,
)
import Zope2
from Products.CMFCore.interfaces import ISiteRoot
from node.ext.ldap.interfaces import (
    ILDAPProps,
    ILDAPUsersConfig,
    ILDAPGroupsConfig,
)
from node.ext.ldap import testing as ldaptesting


SITE_OWNER_NAME = SITE_OWNER_PASSWORD = 'admin'


@implementer(ILDAPProps)
@adapter(Interface)
def ldapprops(context):
    return ldaptesting.props


@implementer(ILDAPUsersConfig)
@adapter(Interface)
def usersconfig(context):
    return ldaptesting.LDIF_groupOfNames_10_10.ucfg


@implementer(ILDAPGroupsConfig)
@adapter(Interface)
def groupsconfig(context):
    return ldaptesting.LDIF_groupOfNames_10_10.gcfg


class PASLDAPLayer(Layer):
    # big parts copied from p.a.testing!

    defaultBases = (ldaptesting.LDIF_groupOfNames_10_10, z2.STARTUP)

    # Products that will be installed, plus options
    products = (
            ('Products.GenericSetup'                , {'loadZCML': True}, ),
            ('Products.CMFCore'                     , {'loadZCML': True}, ),
            ('Products.PluggableAuthService'        , {'loadZCML': True}, ),
            ('Products.PluginRegistry'              , {'loadZCML': True}, ),
            ('Products.PlonePAS'                    , {'loadZCML': True}, ),
        )

    def setUp(self):
        self['zodbDB'] = zodb.stackDemoStorage(self.get('zodbDB'),
                                               name='PASLDAPLayer')
        self['app'] = z2.addRequestContainer(Zope2.app(self['zodbDB'].open()),
                                             environ=None)
        self.setUpZCML()
        self.setUpProducts(self['app'])
        self.setUpDefaultContent(self['app'])

    def tearDown(self):
        self.tearDownProducts(self['app'])
        self.tearDownZCML()
        del self['app']
        self['zodbDB'].close()
        del self['zodbDB']


    def setUpZCML(self):
        """Stack a new global registry and load ZCML configuration of Plone
        and the core set of add-on products into it.
        """
        # Create a new global registry
        zca.pushGlobalRegistry()

        from zope.configuration import xmlconfig
        self['configurationContext'] = context = zca.stackConfigurationContext(
                                               self.get('configurationContext'))

        # Load dependent products's ZCML
        from zope.dottedname.resolve import resolve

        def loadAll(filename):
            for p, config in self.products:
                if not config['loadZCML']:
                    continue
                try:
                    package = resolve(p)
                except ImportError:
                    continue
                try:
                    xmlconfig.file(filename, package, context=context)
                except IOError:
                    pass

        loadAll('meta.zcml')
        loadAll('configure.zcml')
        loadAll('overrides.zcml')
        provideAdapter(ldapprops)
        provideAdapter(usersconfig)
        provideAdapter(groupsconfig)
        provideUtility(self['app'], provides=ISiteRoot)

    def tearDownZCML(self):
        """Pop the global component registry stack, effectively unregistering
        all global components registered during layer setup.
        """
        # Pop the global registry
        zca.popGlobalRegistry()

        # Zap the stacked configuration context
        del self['configurationContext']

    def setUpProducts(self, app):
        """Install all old-style products listed in the the ``products`` tuple
        of this class.
        """
        for p, config in self.products:
            z2.installProduct(app, p)

    def tearDownProducts(self, app):
        """Uninstall all old-style products listed in the the ``products``
        tuple of this class.
        """
        for p, config in reversed(self.products):
            z2.uninstallProduct(app, p)

    def setUpDefaultContent(self, app):
        """Add the site owner user to the root user folder."""

        # Create the owner user and "log in" so that the site object gets
        # the right ownership information
        app['acl_users'].userFolderAddUser(
                SITE_OWNER_NAME,
                SITE_OWNER_PASSWORD,
                ['Manager'],
                []
            )
