#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    'datacube', 'flask',
    ('dea-proto @ git+https://github.com/opendatacube/dea-proto.git'
     '@02b531d3cba9dad3bcccce44e90628bf69fef5b4'
     '#egg=dea-proto')
]

test_requirements = [
    # TODO: put package test requirements here
    'pytest', 'pytest-cov', 'pytest_localserver', 'owslib', 'mock', 'pep8', 'pylint==1.6.4',
]

setup(
    name='datacube_ows',
    version='0.2.0',
    description="Datacube Open Web Services",
    long_description=readme + '\n\n' + history,
    author="Open Data Cube",
    author_email='earth.observation@ga.gov.au',
    url='https://github.com/opendatacube/datacube-wms',
    entry_points={
        'console_scripts': [
            'datacube-ows=datacube_ows.wms_wsgi.__main__:main'
        ]
    },
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
    license="Apache Software License 2.0",
    zip_safe=False,
    keywords='datacube, wms, wcs',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.5',
    ],
    test_suite='tests',
    tests_require=test_requirements
)
