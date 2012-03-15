# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 Everbread, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import os
import re
from setuptools import setup, find_packages


ROOT = os.path.dirname(__file__)

def read(fname):
    return open(os.path.join(ROOT, fname)).read()


INSTALL_REQUIRES = (
	'pika',
	'django>=1.3',
)

TEST_REQUIRES = (
	'mox',
)

setup(name="eventbrain",
      version="0.1",
      url='https://github.com/everbread/EventBrain',
      license='Apache 2.0',
      description="EventBrain library",
      long_description=read('README.rst'),
      author='Everbread',
      author_email='github@everbread.com',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=INSTALL_REQUIRES,
      tests_require=TEST_REQUIRES,
      classifiers=['Development Status :: 4 - Beta',
                   'Framework :: Python',
                   'Intended Audience :: Developers, System administrators',
                   'License :: OSI Approved :: Apache Software License',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python',
                   'Topic :: Internet :: WWW/HTTP']
)

