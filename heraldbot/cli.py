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

import argparse
import configparser
import logging
import os
import sys

from .server import BotServer

LOG = logging.getLogger('heraldbot')

def main():
  parser = argparse.ArgumentParser(
    description = "Discord notification bot",
  )

  parser.add_argument(
    '-l', '--log-level', metavar = 'level', default = 'info',
    help = 'the log output level for the console',
    choices = ['critical', 'error', 'warning', 'info', 'debug'],
  )

  parser.add_argument(
    '-c', '--config', metavar = 'file', required = True,
    help = 'path to the configuration file',
  )

  args = parser.parse_args()

  logLevel = getattr(logging, args.log_level.upper())
  if not isinstance(logLevel, int):
    print('invalid log level', file=sys.stderr)
    sys.exit(1)

  logging.basicConfig(
    level = logLevel,
    stream = sys.stderr,
    format = "%(asctime)s [%(name)s] %(levelname)s: %(message)s",
  )

  config = configparser.ConfigParser()
  try:
    LOG.info("loading config file '%s'", args.config)
    with open(args.config, 'r') as stream:
      config.read_file(stream)
  except OSError as ex:
    LOG.error('failed to read config: %s', ex.strerror)
    sys.exit(1)
  except configparser.Error as ex:
    LOG.error('error in config: %s', str(ex))
    sys.exit(1)


  server = BotServer(config)
  server.run()
