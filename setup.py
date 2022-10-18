#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2021 OWS Contributors
# SPDX-License-Identifier: Apache-2.0

from setuptools import find_packages, setup

install_requirements = [
    'datacube[performance,s3]>=1.8.7',
    'flask',
    'flask_log_request_id',
    'requests',
    'affine',
    'click',
    'colour',
    'fsspec',
    'lxml',
    'deepdiff',
    'matplotlib',
    'pyparsing>=2.2.1,<3',  # resolving dependency conflict between matplotlib and packaging
    'numpy',
    'scipy',
    'Pillow',
    'Babel',
    'Flask-Babel',
    'psycopg2',
    'python_dateutil',
    'pytz',
    'rasterio>=1.3.2',
    'regex',
    'timezonefinderL',
    'python_slugify',
    'geoalchemy2',
    'lark',
    'xarray!=2022.6.0',
    'pyows',
    'prometheus_flask_exporter',
    'setuptools_scm'
]

test_requirements = [
    'pytest', 'pytest_cov', 'pytest_localserver',
    'owslib', 'pytest_mock', 'pep8',
    'pytest-helpers-namespace', 'flask-cors',
    'fsspec',
]

dev_requirements = [
    'pydevd-pycharm~=221.5921.27', # For Pycharm 2022.1.3
    'pylint==2.4.4',
    'sphinx_click',
    'pre-commit==2.13.0',
    'pipdeptree'
]

operational_requirements = [
    "gunicorn", "gunicorn[gevent]", "gevent", "prometheus_client", "sentry_sdk",
    "prometheus_flask_exporter", "blinker"
]
setup_requirements = ['setuptools_scm', 'setuptools']

extras = {
    "dev": dev_requirements + test_requirements + operational_requirements,
    "test": test_requirements,
    "ops": operational_requirements,
    "setup": setup_requirements,
    "all": dev_requirements + test_requirements + operational_requirements,
}

#  Dropped requirements: ruamel.yaml, bottleneck, watchdog

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
            'datacube-ows-update=datacube_ows.update_ranges_impl:main',
            'datacube-ows-cfg=datacube_ows.cfg_parser_impl:main'
        ]
    },
    python_requires=">=3.8.0",
    packages=find_packages(exclude=["tests", "tests.cfg", "integration_tests", "integration_tests.cfg"]),
    include_package_data=True,
    install_requires=install_requirements,
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
    setup_requires=setup_requirements,
    use_scm_version={
        "version_scheme": "post-release",
    },
    test_suite='tests',
    tests_require=test_requirements,
    extras_require=extras
)
