from setuptools import find_packages
from setuptools import setup

import os


version = "1.8.0"
shortdesc = "LDAP/AD Plugin for Plone/Zope PluggableAuthService (users+groups)"
longdesc = open(os.path.join(os.path.dirname(__file__), "README.rst")).read()
longdesc += open(os.path.join(os.path.dirname(__file__), "TODO.rst")).read()
longdesc += open(os.path.join(os.path.dirname(__file__), "CHANGES.rst")).read()
longdesc += open(os.path.join(os.path.dirname(__file__), "LICENSE.rst")).read()


setup(
    name="pas.plugins.ldap",
    version=version,
    description=shortdesc,
    long_description=longdesc,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Framework :: Plone :: 5.1",
        "Framework :: Plone :: 5.2",
        "Framework :: Plone :: Addon",
        "Framework :: Plone",
        "Framework :: Zope :: 2",
        "Framework :: Zope :: 4",
        "Framework :: Zope",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python",
        "Topic :: System :: Systems Administration :: Authentication/Directory :: LDAP"
    ],
    keywords="zope pas plone ldap authentication plugin",
    author="BlueDynamics Alliance",
    author_email="dev@bluedynamics.com",
    url="https://github.com/collective/pas.plugins.ldap/",
    license="GPLv2",
    packages=find_packages("src"),
    package_dir={"": "src"},
    namespace_packages=["pas", "pas.plugins"],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "AccessControl>=3.0",
        "Acquisition",
        "bda.cache",
        "five.globalrequest",
        "node",
        "node.ext.ldap>=1.0b12",
        "odict",
        "plone.registry",
        "Products.CMFCore",
        "Products.GenericSetup",
        "Products.PlonePAS",
        "Products.PluggableAuthService",
        "Products.statusmessages",
        "python-ldap>=3.2.0",
        "setuptools",
        "six",
        "yafowil>=2.3.1",
        "yafowil.plone>=4.0.0a3",
        "yafowil.widget.array",
        "yafowil.widget.dict",
        "yafowil.yaml",
        "zope.component",
        "zope.globalrequest",
        "zope.i18nmessageid",
        "zope.interface",
        "zope.traversing"
    ],
    extras_require={
        "test": ["plone.testing", "zope.configuration"],
        "plone": ["Plone"]
    },
    entry_points="""
    [z3c.autoinclude.plugin]
    target = plone
    """
)
