from setuptools import setup, find_packages
import sys, os

version = '0.1'
shortdesc ="Zope 2 PAS Plugin providing users and groups from LDAP directory"
longdesc = open(os.path.join(os.path.dirname(__file__), 'README.txt')).read()

setup(name='bda.pasldap',
      version=version,
      description=shortdesc,
      long_description=longdesc,
      classifiers=[
            'Environment :: Web Environment',
            'Framework :: Zope2',
            'Operating System :: OS Independent',
            'Programming Language :: Python',           
      ], # Get strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      keywords='zope2',
      author='Florian Friesdorf',
      author_email='flo@chaoflow.net',
      url='',
      license='',
      packages=find_packages('src'),
      package_dir = {'': 'src'},
      namespace_packages=['bda'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools', 
          # -*- Extra requirements: -*
          'Plone', # ? should be required by plone.app.folder but isnt
          'Products.PlonePAS',
          'bda.ldap>=1.6.0',
      ],
      extras_require={
          'test': [
              'interlude',
              'zope.configuration',
              'zope.testing',
          ]
      },
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
