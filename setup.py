#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    'datacube', 'flask', 'dea-proto'
]

test_requirements = [
    # TODO: put package test requirements here
    'pytest', 'pytest-cov', 'pytest_localserver', 'owslib', 'mock', 'pep8', 'pylint==1.6.4',
]

setup(
    name='datacube_wms',
    version='0.1.1',
    description="Datacube Web Map Service",
    long_description=readme + '\n\n' + history,
    author="Open Data Cube",
    author_email='earth.observation@ga.gov.au',
    url='https://github.com/opendatacube/datacube-wms',
    entry_points={
        'console_scripts': [
            'datacube-wms=datacube_wms.wms_wsgi.__main__:main'
        ]
    },
    include_package_data=True,
    install_requires=requirements,
    license="Apache Software License 2.0",
    zip_safe=False,
    keywords='datacube, wms',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.5',
    ],
    test_suite='tests',
    tests_require=test_requirements,
    dependency_links=['git+https://github.com/opendatacube/dea-proto.git@stable#egg=dea-proto-0.2']
)
