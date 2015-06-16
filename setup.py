#!/usr/bin/env python
# encoding: utf-8
from __future__ import absolute_import, print_function
from setuptools import find_packages
import os

# def rpath(*start_paths):
#     packages = set()
#     for start_path in start_paths:
#         if os.path.exists(os.path.join(start_path, '__init__.py')):
#             packages.add(start_path)
#             for cdir, dirs, files in os.walk(start_path):
#                 for d in dirs:
#                     path = os.path.join(cdir, d)
#                     if os.path.exists(os.path.join(path, '__init__.py')):
#                         packages.add(path.replace(os.sep, "."))
#     return list(packages)

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


__version__ = '0.3.0'
__author__ = 'Dmitry Orlov <me@mosquito.su>'


supports = {
    'install_requires': [
        'tornado',
        'arconfig',
        'crew>=0.8.9',
        'gitpython',
        'docker-py',
        'arrow'
    ]
}

setup(
    name='lumper',
    version=__version__,
    author=__author__,
    author_email='me@mosquito.su',
    license="MIT",
    description="Containers builder for docker.",
    platforms="all",
    url="http://github.com/mosquito/lumper",
    classifiers=[
        'Environment :: Console',
        'Programming Language :: Python',
    ],
    scripts=['bin/lumper'],
    # package_data={
    #     'lumper.some': ['rc/*'],
    # },
    long_description=open('README.rst').read(),
    packages=find_packages(),
    **supports
)
