import os
from setuptools import (
    setup,
    find_packages,
)

version = '1.5.2.dev0'
shortdesc = "LDAP/AD Plugin for Plone/Zope PluggableAuthService (users+groups)"
longdesc = open(os.path.join(os.path.dirname(__file__), 'README.rst')).read()
longdesc += open(os.path.join(os.path.dirname(__file__), 'TODO.rst')).read()
longdesc += open(os.path.join(os.path.dirname(__file__), 'CHANGES.rst')).read()
longdesc += open(os.path.join(os.path.dirname(__file__), 'LICENSE.rst')).read()


setup(
    name='pas.plugins.ldap',
    version=version,
    description=shortdesc,
    long_description=longdesc,
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Zope2',
        'Framework :: Plone',
        'Framework :: Plone :: 5.0',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
    ],
    keywords='zope2 pas plone ldap authentication',
    author='BlueDynamics Alliance',
    author_email='dev@bluedynamics.com',
    url='https://pypi.python.org/pypi/pas.plugins.ldap',
    license='BSD like',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    namespace_packages=['pas', 'pas.plugins'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'AccessControl>=3.0',
        'Acquisition',
        'bda.cache',
        'five.globalrequest',
        'node',
        'node.ext.ldap>=1.0b2',
        'odict',
        'plone.registry',
        'Products.CMFCore',
        'Products.GenericSetup',
        'Products.PlonePAS',
        'Products.PluggableAuthService',
        'Products.statusmessages',
        'python-ldap',
        'setuptools',
        'yafowil>=2.2b2',
        'yafowil.plone>=1.3',
        'yafowil.widget.array',
        'yafowil.widget.dict',
        'yafowil.yaml',
        'zope.component',
        'zope.globalrequest',
        'zope.i18nmessageid',
        'zope.interface',
        'zope.traversing',
        'Zope2',
    ],
    extras_require={
        'test': [
            'interlude[ipython]>=1.3.1',
            'plone.testing',
            'zope.configuration',
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
