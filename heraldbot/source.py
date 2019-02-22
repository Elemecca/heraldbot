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
import aioredis
import datetime
import logging

LOG = logging.getLogger('heraldbot')

class PollingSource(object):
  interval = 5 * 60
  redis_url = 'redis://localhost'
  max_age = datetime.timedelta(days=1)

  def __init__(self, config=None, name=None, discord=None):
    self.name = name
    self.discord = discord

    if 'interval' in config:
      self.interval = int(config['interval'])

    if 'redis_url' in config:
      self.redis_url = config['redis_url']

    if 'max_age_days' in config or 'max_age_seconds' in config:
      self.max_age = datetime.timedelta(
        days=config.getint('max_age_days', 0),
        seconds=config.getint('max_age_seconds', 0),
      )

    self.mark_all = config.getboolean('mark_all_handled', False)


  async def run(self):
    LOG.info(
      "[%s] %s poller starting, interval %d",
      self.name, self.TYPE, self.interval
    )

    self.redis = await aioredis.create_redis(self.redis_url)

    await self.prepare()

    while True:
      # the sleep runs concurrently with the polling action
      # which makes the polling interval much closer to nominal
      # awaiting the poll ensures that invocations don't overlap
      sleep = asyncio.sleep(self.interval)
      LOG.debug("[%s] polling %s", self.name, self.TYPE)
      await self.poll()
      await sleep

  def _redisKey(self, id):
    return (
      'heraldbot.' + self.name.lower()
      + '.msg.' + str(id).lower()
    )

  async def should_handle(self, id, timestamp):
    LOG.debug(
      "[%s] checking msg %s from %s",
      self.name, str(id), timestamp.isoformat()
    )

    now = datetime.datetime.now(datetime.timezone.utc)
    if timestamp + self.max_age < now:
      return False

    if await self.redis.get(self._redisKey(id)):
      return False

    if self.mark_all:
      LOG.info(
        "[%s] mark_all_handled %s from %s",
        self.name, str(id), timestamp.isoformat()
      )
      await self.mark_handled(id, timestamp)
      return False

    return True

  async def mark_handled(self, id, timestamp):
    LOG.debug(
      "[%s] handled msg %s from %s",
      self.name, str(id), timestamp.isoformat()
    )

    await self.redis.set(self._redisKey(id), timestamp.isoformat())
