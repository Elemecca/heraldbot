# HeraldBot - polling notification bot for Discord
# Written in 2018 by Sam Hanes <sam@maltera.com>
#
# To the extent possible under law, the author(s) have dedicated all
# copyright and related and neighboring rights to this software to the
# public domain worldwide. This software is distributed without any warranty.
#
# You should have received a copy of the CC0 Public Domain Dedication
# along with this software. If not, see
# <http://creativecommons.org/publicdomain/zero/1.0/>.

from setuptools import setup

setup(
  name='heraldbot',
  version='0.1',
  author='Sam Hanes',
  author_email='sam@maltera.com',
  description='polling notification bot for Discord',
  url='https://github.com/Elemecca/heraldbot',
  license='CC0',
  python_requires='>=3.5',
  entry_points={
    'console_scripts': [
      'heraldbot=heraldbot.cli:main',
    ],
  },
  install_requires=[
    'aiohttp',
    'aioredis',
    'html2text',
  ],
  classifiers=[
    'Development Status :: 3 - Alpha',
    'Environment :: Console',
    'Framework :: AsyncIO',
    'License :: CC0 1.0 Universal (CC0 1.0) Public Domain Dedication',
    'License :: Public Domain',
    'Topic :: Communications :: Chat',
  ],
)
