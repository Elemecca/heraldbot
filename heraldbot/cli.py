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
import os
import logging

from .server import BotServer

LOG = logging.getLogger(__name__)

def main(argv):
  parser = argparse.ArgumentParser(
    description = "Discord notification bot",
  )

  parser.add_argument(
    '--config', '-c', metavar = 'file',
    help = 'path to the configuration file',
  )

  args = parser.parse_args(argv[1:])

  logging.basicConfig(
    level = logging.DEBUG,
    format = "%(asctime)s [%(name)s] %(levelname)s: %(message)s",
  )

  if args.config is None:
    script = os.path.abspath(argv[0])
    args.config = os.path.join(os.path.dirname(script), 'heraldbot.cfg')

  LOG.info("loading config file %s", args.config)
  config = configparser.ConfigParser()
  config.read(args.config)


  server = BotServer()
  server.configure(config)
  server.run()
