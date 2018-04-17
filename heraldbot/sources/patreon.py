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
import datetime
from html2text import HTML2Text
import logging
import re
import textwrap

from heraldbot.source import PollingSource

LOG = logging.getLogger('heraldbot')

STREAM_URL = 'https://www.patreon.com/api/stream'
LOGIN_URL = 'https://www.patreon.com/api/login'
LOGIN_FORM_URL = 'https://www.patreon.com/login'
LOGO_URL = 'https://c5.patreon.com/external/logo/downloads_logomark_color_on_coral.png'


class InaccessiblePostError(Exception):
  """The polling process encountered a locked post."""


def mangleBody(text):
  h2 = HTML2Text()
  h2.body_width = None
  h2.ignore_links = True
  h2.ignore_images = True

  return textwrap.shorten(h2.handle(text), width=250)

def convertPost(post, author):
  title = post['attributes']['title']

  body = None
  if 'content' in post['attributes']:
    body = mangleBody(post['attributes']['content'])

  embed = {
    'type': 'rich',
    'color': 0xf96854,
    'url': post['attributes']['url'],
    'title': title if title else 'Community Post',
    'timestamp': post['attributes']['published_at'],
    'description': body,
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
    image = post['attributes']['image']
    embed['thumbnail'] = {'url': image['large_url']}

  return embed

class Source(PollingSource):
  TYPE = "Patreon"

  def __init__(self, config=None, http_con=None, **kwargs):
    super().__init__(config=config, **kwargs)

    self.creator_id = config['patreon.creator_id']
    self.username = config['patreon.username']
    self.password = config['patreon.password']

    self.http = aiohttp.ClientSession(
      connector=http_con,
      conn_timeout=15,
      read_timeout=60,
      raise_for_status=True,
    )


  async def prepare(self):
    await self._login()

  async def _login(self):
    await self.http.post(
      LOGIN_URL,
      params={
        'json-api-version': '1.0',
      },
      headers={
        'Content-Type': 'application/vnd.api+json',
      },
      json={
        'data': {
          'type': 'user',
          'attributes': {
            'email': self.username,
            'password': self.password,
          },
        },
      }
    )


  async def poll(self):
    try:
      try:
        await self._poll(creatorPosts=True)
        await self._poll(creatorPosts=False)

      except InaccessiblePostError:
        await self._login()
        await self._poll(retry=True, creatorPosts=True)
        await self._poll(retry=True, creatorPosts=False)

    except:
      LOG.exception("[%s] failed polling %s", self.name, self.TYPE)


  async def _poll(self, creatorPosts=True, retry=False):
    resp = await self.http.get(STREAM_URL, params={
      'include': 'user',
      'fields[post]': ','.join([
        'title',
        'published_at',
        'current_user_can_view',
        'content',
        'image',
        'url',
      ]),
      'fields[user]': ','.join([
        'full_name',
        'image_url',
        'url',
      ]),
      'filter[creator_id]': self.creator_id,
      'filter[is_by_creator]': 'true' if creatorPosts else 'false',
      'filter[contains_exclusive_posts]': 'true',
      'json-api-use-default-includes': 'false',
      'json-api-version': '1.0',
    })

    LOG.debug("[%s] fetched %s", self.name, resp.url)

    body = await resp.json(content_type='application/vnd.api+json')

    for post in body['data']:
      id = post['id']

      # parse the RFC 3339 / ISO 8601 date string
      # using regexes to compensate for strptime's shortcomings
      # by stripping separators and converting 'Z' to '+0000'
      timestr = post['attributes']['published_at']
      timestamp = datetime.datetime.strptime(
        re.sub(r':|-(?=.*T)', '', re.sub(r'Z$', '+0000', timestr)),
        '%Y%m%dT%H%M%S%z'
      )

      if await self.should_handle(id, timestamp):
        if not post['attributes']['current_user_can_view'] and not retry:
          raise InaccessiblePostError()

        LOG.info("[%s] announcing post %s", self.name, str(id))

        user = next(
          inc for inc in body['included']
            if inc['type'] == 'user'
            and inc['id'] == post['relationships']['user']['data']['id']
        )
        message = convertPost(post, user)

        await self.discord.send(embed=message)
        await self.mark_handled(id, timestamp)
