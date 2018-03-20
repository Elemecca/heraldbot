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
import aiohttp
from importlib import import_module
import logging
import sys

from .discord import DiscordSender

LOG = logging.getLogger('heraldbot')


class BotServer(object):
  exit_status = 0

  def __init__(self, config):
    self.loop = asyncio.get_event_loop()
    self.config = config

  async def _prepare(self):
    if not self.config.sections():
      LOG.error("no source sections in config; shutting down")
      return self.stop(status=1)

    self.http_con = aiohttp.TCPConnector(
      limit_per_host=2,
      keepalive_timeout=0,
    )

    sources = []
    for name in self.config.sections():
      section = self.config[name]

      mod_name = section['source'] if 'source' in section else name
      try:
        mod = import_module('heraldbot.sources.' + mod_name)
      except ImportError:
        LOG.error(
          "invalid source '%s'; skipping section '%s'",
          mod_name, name
        )
        continue

      discord = DiscordSender(config=section, http_con=self.http_con)

      source = mod.Source(
        name=name,
        config=section,
        discord=discord,
        http_con=self.http_con,
      )
      self.loop.create_task(source.run())
      sources.append(source)

    if not sources:
      LOG.error("no valid source configurations; shutting down")
      return self.stop(status=1)

  def run(self):
    self.loop.set_exception_handler(self._error)
    self.loop.create_task(self._prepare())
    self.loop.run_forever()
    sys.exit(self.exit_status)

  def _error(self, loop, context):
    loop.default_exception_handler(context)
    LOG.error('unhandled exception in coroutine; shutting down')
    self.stop(status=2)

  def stop(self, status=0):
    self.exit_status = status
    self.loop.stop()
