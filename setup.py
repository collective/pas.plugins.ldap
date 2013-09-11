import os
from setuptools import (
    setup,
    find_packages,
)


version = '1.0.2'
shortdesc = "LDAP Plugin for Zope2 PluggableAuthService (users and groups)"
longdesc = open(os.path.join(os.path.dirname(__file__), 'README.rst')).read()
longdesc += open(os.path.join(os.path.dirname(__file__), 'TODO.rst')).read()
longdesc += open(os.path.join(os.path.dirname(__file__), 'HISTORY.rst')).read()
longdesc += open(os.path.join(os.path.dirname(__file__), 'LICENSE.rst')).read()


setup(name='pas.plugins.ldap',
      version=version,
      description=shortdesc,
      long_description=longdesc,
      classifiers=[
          'Environment :: Web Environment',
          'Framework :: Zope2',
          'Operating System :: OS Independent',
          'Programming Language :: Python',
      ],
      keywords='zope2 pas plone ldap',
      author='BlueDynamics Alliance',
      author_email='dev@bluedynamics.com',
      url='https://github.com/collective/pas.plugins.ldap',
      license='BSD like',
      packages=find_packages('src'),
      package_dir={'': 'src'},
      namespace_packages=['pas', 'pas.plugins'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'AccessControl',
          'Acquisition',
          'Products.CMFCore',
          'Products.PlonePAS',
          'Products.PluggableAuthService',
          'Zope2',
          'bda.cache',
          'five.globalrequest',
          'python-ldap',
          'node',
          'node.ext.ldap',
          'odict',
          'setuptools',
          'yafowil.plone>=1.3',
          'yafowil.widget.array',
          'yafowil.widget.dict',
          'yafowil.yaml',
          'zope.component',
          'zope.globalrequest',
          'zope.i18nmessageid',
          'zope.interface',
          'zope.traversing',
          # for controlpanel
          'ZODB3',
          'Products.CMFQuickInstallerTool',
          'Products.GenericSetup',
          'Products.statusmessages',
          'persistent',
          'plone.registry',
          'yafowil',
      ],
      extras_require={
          'test': [
              'interlude',
              'zope.configuration',
              'plone.testing',
          ],
          'plone': [
              'Plone',
          ]
      },
      entry_points="""
      [z3c.autoinclude.plugin]
      target = plone
      """,
      )
