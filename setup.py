from setuptools import setup, find_packages
import sys, os

version = '1.0.beta'
shortdesc ="Zope 2 PAS Plugin providing users and groups from LDAP directory"
longdesc = open(os.path.join(os.path.dirname(__file__), 'README.rst')).read()

setup(name='pas.plugins.ldap',
      version=version,
      description=shortdesc,
      long_description=longdesc,
      classifiers=[
            'Environment :: Web Environment',
            'Framework :: Zope2',
            'Operating System :: OS Independent',
            'Programming Language :: Python',           
      ], # Get strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      keywords='zope2 pas plone',
      author='BlueDynamics Alliance',
      author_email='dev@bluedynamics.com',
      url='https://github.com/bluedynamics/pas.plugins.ldap',
      license='',
      packages=find_packages('src'),
      package_dir = {'': 'src'},
      namespace_packages=['pas', 'pas.plugins'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools', 
          'Products.PlonePAS',
          'node.ext.ldap',
          'yafowil.zope2',
          'yafowil.widget.dict',
          'yafowil.yaml',              
      ],
      extras_require={
          'test': [
              'interlude',
              'zope.configuration',
              'zope.testing',
              'plone.testing',
          ],
          'plone': [
              'Plone',
              'yafowil.zope2',
              'yafowil.widget.dict',
              'yafowil.yaml',              
          ]
      },
      entry_points="""
      [z3c.autoinclude.plugin]
      target = plone
      """,     
      )