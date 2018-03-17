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

import aiohttp
import json
import logging

LOG = logging.getLogger(__name__)

class DiscordSender(object):
  def __init__(self):
    self.url = None
    self.body = {
      'wait': True,
    }

  def configure(self, config):
    self.url = config['discord.webhook']

    if 'discord.username' in config:
      self.body['username'] = config['discord.username']

    if 'discord.avatar_url' in config:
      self.body['avatar_url'] = config['discord.avatar_url']



  async def send(self, content=None, embed=None):
    async with aiohttp.ClientSession() as http:
      body = self.body.copy()

      if content:
        body['content'] = content

      if embed:
        body['embeds'] = [embed]

      LOG.debug("sending webhook:\n%s", json.dumps(body, indent=2))

      async with http.post(self.url, json=body) as res:
        res.raise_for_status()
