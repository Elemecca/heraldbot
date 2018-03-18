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
from html2text import HTML2Text
import logging
from textwrap import TextWrapper

from heraldbot.source import PollingSource

LOG = logging.getLogger(__name__)

STREAM_URL = 'https://www.patreon.com/api/stream'
LOGO_URL = 'https://c5.patreon.com/external/logo/downloads_logomark_color_on_coral.png'

def mangleBody(text):
  h2 = HTML2Text()
  h2.body_width = None
  h2.ignore_links = True
  h2.ignore_images = True

  wrap = TextWrapper()
  wrap.width = 200
  wrap.max_lines = 1
  wrap.replace_whitespace = False

  short = wrap.fill(h2.handle(text))
  shorter = '\n'.join(short.split('\n')[:3])
  if shorter != short:
    shorter = shorter + ' [...]'
  return shorter

def convertPost(post, author):
  title = post['attributes']['title']
  embed = {
    'type': 'rich',
    'color': 0xf96854,
    'url': post['attributes']['url'],
    'title': title if title else 'Community Post',
    'timestamp': post['attributes']['published_at'],
    'description': mangleBody(post['attributes']['content']),
    'author': {
      'name':     author['attributes']['full_name'],
      'url':      author['attributes']['url'],
      'icon_url': author['attributes']['image_url'],
    },
    'footer': {
      'text': 'Patreon',
      'icon_url': LOGO_URL,
    },
  }

  if (post['attributes']['image']):
    embed['thumbnail'] = {
      'url':    post['attributes']['image']['large_url'],
      'height': post['attributes']['image']['height'],
      'width':  post['attributes']['image']['width'],
    }

  return embed

def authorForPost(post, included):
  return next(
    inc for inc in included
      if inc['type'] == 'user'
      and inc['id'] == post['relationships']['user']['data']['id']
  )

def params(creatorPosts = True):
  return {
    'include': 'user',
    'fields[post]': ','.join([
      'title',
      'published_at',
      #'post_type',
      'content',
      'image',
      #'embed',
      'url',
    ]),
    'fields[user]': ','.join([
      'full_name',
      'image_url',
      'url',
    ]),
    'filter[creator_id]': 136449,
    'filter[is_by_creator]': 'true' if creatorPosts else 'false',
    'json-api-use-default-includes': 'false',
    'json-api-version': '1.0',
  }


class Source(PollingSource):
  TYPE = "Patreon"
  cookies = {}

  def __init__(self, **kwargs):
    super().__init__(**kwargs)

  def configure(self, config):
    super().configure(config)

    self.cookies['session_id'] = config['patreon.session_id']


  async def prepare(self):
    pass


  async def poll(self):
    async with aiohttp.ClientSession(cookies=self.cookies) as session:
      resp = await session.get(STREAM_URL, params=params(creatorPosts=False))
      print(str(resp.url))

      body = await resp.json(content_type='application/vnd.api+json')

      post = body['data'][0]
      user = authorForPost(post, body['included'])
      message = convertPost(post, user)

      await self.discord.send(embed=message)
