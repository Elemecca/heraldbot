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

import asyncio
from importlib import import_module
import logging
import sys

from .discord import DiscordSender

LOG = logging.getLogger(__name__)


class BotServer(object):
  loop = None
  source = None

  def __init__(self):
    self.loop = asyncio.get_event_loop()


  def configure(self, config):
    self.config = config

    if not config.sections():
      LOG.error("no source sections in config; shutting down")
      sys.exit(1)

    sources = []
    for name in config.sections():
      section = config[name]

      mod_name = section['source'] if 'source' in section else name
      try:
        mod = import_module('heraldbot.sources.' + mod_name)
      except ImportError:
        LOG.error(
          "invalid source '%s'; skipping section '%s'",
          mod_name, name
        )
        continue

      discord = DiscordSender()
      discord.configure(section)

      source = mod.Source(name=name, discord=discord)
      source.configure(section)

      self.loop.create_task(source.run())
      sources.append(source)

    if not sources:
      LOG.error("no valid source configurations; shutting down")
      sys.exit(1)

  def run(self):
    self.loop.run_forever()

  def stop(self):
    self.loop.stop()
