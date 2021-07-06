#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='aedat4to2',
      version='1.0',
      description='Converts AEDAT-4 from DV to AEDAT-2 for jAER',
      author='Tobi Delbruck',
      author_email='tobi@ini.uzh.ch',
      url='https://github.com/SensorsINI/aedat4to2',
      packages=find_packages(include=['aedat4to2', 'aedat4to2.*']),
      install_requires=[
            'numpy','argparse','dv'
      ],
      entry_points = {
            'console_scripts': ['aedat4to2=aedat4to2.aedat4to2:main']
      }
)
