#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

requirements = [
    'datacube',
    'Flask',
    'flask_log_request_id',
    'requests',
    'affine',
    'click',
    'colour',
    'lxml',
    'matplotlib',
    'numpy',
    'Pillow',
    'prometheus_client',
    'psycopg2',
    'python_dateutil',
    'pytz',
    'rasterio',
    'regex',
    'scikit-image',
    'timezonefinderL',
    'python-slugify',
    'geoalchemy',
    'xarray',
    'pyows',
    'prometheus-flask-exporter',
    #
    'setuptools_scm'
]

test_requirements = [
    # TODO: put package test requirements here
    'pytest', 'pytest-cov', 'pytest_localserver', 'owslib', 'mock', 'pep8', 'pylint==1.6.4', 'pytest-helpers-namespace'
]

setup(
    name='datacube_ows',
    description="Open Data Cube Open Web Services",
    long_description="""
============
datacube-ows
============

Open Web Services for the Open Datacube.

* Free software: Apache Software License 2.0
* Documentation: https://datacube-ows.readthedocs.io.

Features
--------

* Leverages the power of the Open Data Cube, including support for COGs on S3.
* Supports WMS and WMTS.
* Experimental support for WCS (1.0, 2.0, 2.1).
    
    """,
    author="Open Data Cube",
    author_email='earth.observation@ga.gov.au',
    url='https://github.com/opendatacube/datacube-ows',
    entry_points={
        'console_scripts': [
            'datacube-ows=datacube_ows.wsgi:main',
            'datacube-ows-update=datacube_ows.update_ranges:main',
            'datacube-ows-cfg-parse=datacube_ows.cfg_parser:main'
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
    setup_requires=['setuptools_scm'],
    use_scm_version=True,
    test_suite='tests',
    tests_require=test_requirements
)
