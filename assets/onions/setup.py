#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from setuptools import find_packages
from setuptools import setup

setup(
    name='onions',

    version='0.2',

    packages=find_packages(),

    author="Christophe Mehay",

    author_email="cmehay@nospam.student.42.fr",

    description="Display onion sites hosted",

    include_package_data=True,

    url='http://github.com/cmehay/docker-tor-hidden-service',

    classifiers=[
        "Programming Language :: Python",
        "Development Status :: 1 - Planning",
        "License :: OSI Approved :: BSD License",
        "Natural Language :: English",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Topic :: System :: Installation/Setup",
    ],

    install_requires=['pyentrypoint',
                      'Jinja2>=2.8',
                      'pycrypto',],

    entry_points={
        'console_scripts': [
            'onions = onions:main',
        ],
    },

    license="WTFPL",
)
