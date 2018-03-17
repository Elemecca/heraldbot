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
import logging
import sys

from .discord import DiscordSender
from .sources.patreon import PatreonSource

LOG = logging.getLogger(__name__)


class BotServer(object):
  loop = None
  source = None

  def __init__(self):
    self.loop = asyncio.get_event_loop()


  def configure(self, config):
    self.config = config

    if not config.sections():
      LOG.error("no provider sections in config; shutting down")
      sys.exit(1)

    section = config['patreon']

    discord = DiscordSender()
    discord.configure(section)

    LOG.info("hello!")
    self.source = PatreonSource(discord=discord)
    self.source.configure(section)
    LOG.info("goodbye!")

  def run(self):
    #self.loop.run_forever()
    self.loop.run_until_complete(self.source.poll())

  def stop(self):
    self.loop.stop()
