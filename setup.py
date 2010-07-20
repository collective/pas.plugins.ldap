from setuptools import setup, find_packages
import sys, os

version = '1.2.3'
shortdesc ="Zope 2 PAS Plugin providing groups from LDAP directory"
longdesc = open(os.path.join(os.path.dirname(__file__), 'README.txt')).read()

setup(name='Products.PASGroupsFromLDAP',
      version=version,
      description=shortdesc,
      long_description=longdesc,
      classifiers=[
            'Development Status :: 5 - Production/Stable',
            'Environment :: Web Environment',
            'Framework :: Zope2',
            'Operating System :: OS Independent',
            'Programming Language :: Python',           
      ], # Get strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      keywords='zope2',
      author='Jens Klein, Robert Niederreiter',
      author_email='jens@bluedynamics.com, rnix@squarewave.at',
      url='',
      license='',
      packages=find_packages('src'),
      package_dir = {'': 'src'},
      namespace_packages=['Products'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools', 
          'bda.ldap>=1.2.1',
          # -*- Extra requirements: -*
      ],
      extras_require={
      },
      entry_points="""
      # -*- Entry points: -*-
      """,
      )

