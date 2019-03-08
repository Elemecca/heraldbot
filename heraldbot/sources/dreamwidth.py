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
import logging
import re
import xml.etree.ElementTree as ET

from heraldbot.source import PollingSource
from heraldbot import util

LOG = logging.getLogger('heraldbot')

DREAMWIDTH_RED = 0xC1272D
LOGO_URL = 'https://www.dreamwidth.org/img/comm_staff.png'

class Source(PollingSource):
  TYPE = "Dreamwidth"

  def __init__(self, config=None, http_con=None, **kwargs):
    super().__init__(config=config, **kwargs)

    self.feed_url = config['dreamwidth.rss_url']

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
    resp = await self.http.get(self.feed_url)
    feed = ET.fromstring(await resp.text()).find('channel');

    LOG.debug("[%s] fetched %s", self.name, resp.url)

    author_name = feed.find('title').text
    author_url = feed.find('link').text
    author_image = feed.find('image').find('url').text

    for entry in feed.findall('item'):
      guid = entry.find('guid').text
      match = re.fullmatch(r'https?://([^./]+)\.dreamwidth\.org/(\d+)\.html', guid)
      if not match:
        raise Error("invalid post guid format '" + guid + "'")

      id = match.group(1) + '.' + match.group(2)
      timestamp = util.parse_2822(entry.find('pubDate').text)

      if await self.should_handle(id, timestamp):
        LOG.info("[%s] announcing post %s", self.name, id)

        content = entry.find('description').text
        text = util.html_to_summary(content)
        image = util.html_get_image(content)

        text = re.sub(r'\s*comments\s*$', '', text)

        embed = {
          'type': 'rich',
          'color': DREAMWIDTH_RED,
          'author': {
            'name': author_name,
            'url': author_url,
            'icon_url': author_image,
          },
          'url': entry.find('link').text,
          'title': entry.find('title').text,
          'timestamp': timestamp.isoformat(),
          'description': text,
          'footer': {
            'text': 'Dreamwidth',
            'icon_url': LOGO_URL,
          },
        }

        if image is not None:
          embed['thumbnail'] = { 'url': image }

        await self.discord.send(embed=embed)
        await self.mark_handled(id, timestamp)
