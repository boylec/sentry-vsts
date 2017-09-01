#coding=utf-8
"""This module installs the Sentry.io VSTS integration plugin"""

from setuptools import setup, find_packages

setup(
    name='sentry_vsts',
    version='0.0.1',
    author='Casey Boyle',
    author_email='boylec@live.com',
    url='https://github.com/boylec/sentry-vsts',
    description='A Sentry.io plugin for Visual Studio Team Services \
    integration',
    keywords='sentry-vsts sentry vsts visual studio team services sentry.io',
    long_description=open('README.rst').read(),
    packages=find_packages(exclude=['tests']),
    install_requires=[
        'sentry>=4.6.0',
        'requests>=0.12.1',
    ],
    dependency_links=[],
    license='MIT',
    include_package_data=True,
    entry_points={
        'sentry.plugins': ['vsts=src.plugin:VstsPlugin']
    },
    classifiers=[
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Operating System :: OS Independent',
        'Topic :: Software Development'
    ],
)
