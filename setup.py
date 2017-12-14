#!/usr/bin/env python
#
# Uses Python Build Reasonableness https://docs.openstack.org/developer/pbr/
# Add configuration to `setup.cfg`

from setuptools import setup

setup(
        # name='mdssdiff',
        # version='dev',
        # url='https://github.com/coecms/mdssdiff',
        # packages=['mdssdiff'],
        setup_requires=['pbr>=1.9', 'setuptools>=17.1'],
        pbr=True,
        # entry_points = {
        #     'console_scripts': [
        #         'mdssdiff=mdssdiff.mdssdiff:main',
        #         ]
        #     },
        )

