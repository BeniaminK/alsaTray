#!/usr/bin/env python

from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

AUTHOR_NAMES=[]
AUTHOR_EMAILS=[]

with open('AUTHORS') as f:
    for line in f:
        import re
        m = re.match(r' *\* (.*) <(.*)>', line)
        if m:
            AUTHOR_NAMES.append(m.group(1))
            AUTHOR_EMAILS.append(m.group(2))

def readme():
     with open('README.rst') as f:
         return f.read()

def get_version():
    from alsa_tray import alsa_tray
    return alsa_tray.__version__


setup(name='ALSATray',
      version=get_version(),
      description='ALSA Tray - Set the volume of the ALSA Master mixer.',
      long_description= readme(),
      url='https://github.com/BeniaminK/alsaTray',
      author=', '.join(AUTHOR_NAMES),
      author_email=', '.join(AUTHOR_EMAILS),
      classifiers=[
        'Development Status :: 5 - Production/Stable'
	'Environment :: Console',
	'Environment :: X11 Applications :: GTK',
	'Intended Audience :: Developers',
	'Intended Audience :: End Users/Desktop',
	'Intended Audience :: System Administrators',
	'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
	'License :: Public Domain',
	'Operating System :: Microsoft :: Windows',
	'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
	'Topic :: Desktop Environment :: Window Managers',
	'Topic :: Multimedia :: Sound/Audio',
	'Topic :: Software Development :: User Interfaces',
	'Topic :: Software Development :: Widget Sets',
	'Topic :: Terminals'
      ],
      keywords='alsa systray tray',
      packages=find_packages(),
      install_requires=['pyalsaaudio'],
      extras_require={
        'all': ['xdg', 'dbus-python', 'pynotify'],
      },
      package_data={
         'code':['../pixmaps/*.png', '*.glade', '../locales/*'],
      },
    entry_points={
        'console_scripts': [
            'alsa-tray=alsa_tray.alsa_tray:main',
        ],
    },
)

