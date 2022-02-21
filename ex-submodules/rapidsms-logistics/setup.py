#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from setuptools import setup, find_packages

setup(
    name='sms_logistics',
    version='0.0.1',
    description='SMS Logistics',
    author='Dimagi',
    author_email='logistics@dimagi.com',
    url='http://www.dimagi.com/',
    packages = find_packages(exclude=['*.pyc']),
    include_package_data=True
)
