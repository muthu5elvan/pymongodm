#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
from pip.req import parse_requirements

install_reqs = parse_requirements("requirements.txt", session=False)
try:
    from pypandoc import convert
    read_md = lambda f: convert(f, 'rst')
except ImportError:
    print("warning: pypandoc module not found")
    read_md = lambda f: open(f, 'r').read()


try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup, find_packages


if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()


try:
    readme = read_md('README.md')
except:
    readme = ""
try:
    changelog = read_md('CHANGELOG.md')
except:
    changelog = ""

setup(
    name='pymongodm',
    version='0.0.5',
    description='pymongodm',
    long_description=readme + '\n\n' + changelog,
    author='GlobalStudio',
    author_email='contacto@globalstudio.es',
    url='https://github.com/GlobalStudioES/pymongodm',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[str(ir.req) for ir in install_reqs],
    license="GPL",
    zip_safe=False,
    keywords='globalstudio, odm, mongo, pymongo',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Programming Language :: Python :: 3',
    ],
)
