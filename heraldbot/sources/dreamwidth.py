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
from email.utils import parsedate_to_datetime
import logging
import xml.etree.ElementTree as ET

from heraldbot.source import PollingSource
from heraldbot import util

LOG = logging.getLogger('heraldbot')

DREAMWIDTH_RED = 0xC1272D
LOGO_URL = 'https://www.dreamwidth.org/img/comm_staff.png'
NS = {
  'a': 'http://www.w3.org/2005/Atom',
  'dw': 'https://www.dreamwidth.org',
}

class Source(PollingSource):
  TYPE = "Dreamwidth"

  def __init__(self, config=None, http_con=None, **kwargs):
    super().__init__(config=config, **kwargs)

    self.feed_url = config['dreamwidth.atom_url']

    self.http = aiohttp.ClientSession(
      connector=http_con,
      conn_timeout=15,
      read_timeout=60,
      raise_for_status=True,
    )

  async def prepare(self):
    pass

  async def stop(self):
    pass

  async def poll(self):
    LOG.debug('dreamwidth poll called')
    resp = await self.http.get(self.feed_url)
    feed = ET.fromstring(await resp.text());

    LOG.debug("[%s] fetched %s", self.name, resp.url)

    for entry in feed.findall('a:entry', NS):
      id = entry.find('a:id', NS).text
      timestamp = util.parse_3339(entry.find('a:published', NS).text)

      if await self.should_handle(id, timestamp):
        LOG.info("[%s] announcing post %s", self.name, str(id))

        embed = {
          'type': 'rich',
          'color': DREAMWIDTH_RED,
          'url': entry.find('./a:link[@type="text/html"]', NS).get('href'),
          'title': entry.find('a:title', NS).text,
          'timestamp': entry.find('a:published', NS).text,
          'description': util.html_to_summary(entry.find('a:content', NS).text),
          'footer': {
            'text': 'Dreamwidth',
            'icon_url': LOGO_URL,
          },
        }

        await self.discord.send(embed=embed)
        await self.mark_handled(id, timestamp)
