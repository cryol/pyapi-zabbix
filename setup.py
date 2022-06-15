#!/usr/bin/env python
from setuptools import setup
from pyapi_zabbix.version import __version__

setup(name='pyapi-zabbix',
      version=__version__,
      description='Python module to work with zabbix.',
      long_description_content_type="text/markdown",
      long_description=open('README.rst', 'r').read(),
      url='https://github.com/cryol/pyapi-zabbix',
      author='Anton Baranov',
      author_email='cryol@cryol.kiev.ua',
      test_suite='tests',
      packages=['pyapi_zabbix'],
      tests_require=['mock'],
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 3',
          'Topic :: System :: Monitoring',
          'Topic :: System :: Networking :: Monitoring',
          'Topic :: System :: Systems Administration'
      ]
      )
