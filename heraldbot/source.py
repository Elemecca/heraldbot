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

LOG = logging.getLogger(__name__)

class PollingSource(object):
  interval = 5 * 60

  def __init__(self, name=None, discord=None):
    self.name = name
    self.discord = discord


  def configure(self, config):
    if 'interval' in config:
      self.interval = int(config['interval'])


  async def run(self):
    LOG.info(
      "%s poller starting for [%s], interval %d",
      self.TYPE, self.name, self.interval
    )

    await self.prepare()

    while True:
      # the sleep runs concurrently with the polling action
      # which makes the polling interval much closer to nominal
      # awaiting the poll ensures that invocations don't overlap
      sleep = asyncio.sleep(self.interval)
      LOG.debug("polling %s for [%s]", self.TYPE, self.name)
      await self.poll()
      await sleep
