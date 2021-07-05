#!/usr/bin/env python

from distutils.core import setup

setup(name='aedat4to2',
      version='1.0',
      description='Converts AEDAT-4 from DV to AEDAT-2 for jAER',
      author='Tobi Delbruck',
      author_email='tobi@ini.uzh.ch',
      url='https://github.com/SensorsINI/aedat4to2',
      packages=['distutils', 'distutils.command'],
      )