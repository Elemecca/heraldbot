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

STREAM_URL     = 'https://www.patreon.com/api/stream'
MONOCLE_URL    = 'https://www.patreon.com/api/monocle-channels/'
LOGIN_URL      = 'https://www.patreon.com/api/login'
LOGIN_FORM_URL = 'https://www.patreon.com/login'
LOGO_URL = 'https://c5.patreon.com/external/logo/downloads_logomark_color_on_coral.png'
PATREON_ORANGE = 0xf96854


class InaccessiblePostError(Exception):
  """The polling process encountered a locked post."""


def parseDate(value):
  """parses an RFC 3339 / ISO 8601 date string"""
  # uses regexes to compensate for strptime's shortcomings

  # convert the `Z` timezone spec to `+0000`
  value = re.sub(r'Z$', '+0000', value)

  # strip all optional separators (colon, hyphen before T)
  value = re.sub(r':|-(?=.*T)', '', value)

  # add microseconds if missing
  value = re.sub(r'(?<!\.\d{6})(?=[+-])', '.000000', value)

  return datetime.datetime.strptime(value, '%Y%m%dT%H%M%S.%f%z')


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
    'color': PATREON_ORANGE,
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


def convertLens(post):
  embed = {
    'type': 'rich',
    'color': PATREON_ORANGE,
    'title': 'Lens Clip',
    'description': 'A new Lens clip has been posted.',
    'timestamp': post['attributes']['published_at'],
    'thumbnail': {'url': post['attributes']['thumbnail_url']},
    'url': post['attributes']['viewing_url'],
    'footer': {
      'text': 'Patreon',
      'icon_url': LOGO_URL,
    },
  }

  return embed


class Source(PollingSource):
  TYPE = "Patreon"

  def __init__(self, config=None, http_con=None, **kwargs):
    super().__init__(config=config, **kwargs)

    self.creator_id = config['patreon.creator_id']
    self.monocle_id = config['patreon.monocle_id']
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
        if self.creator_id is not None:
          await self._pollStream(creatorPosts=True)
          await self._pollStream(creatorPosts=False)
        if self.monocle_id is not None:
          await self._pollMonocle()

      except InaccessiblePostError:
        await self._login()
        if self.creator_id is not None:
          await self._pollStream(retry=True, creatorPosts=True)
          await self._pollStream(retry=True, creatorPosts=False)
        if self.monocle_id is not None:
          await self._pollMonocle(retry=True)

    except:
      LOG.exception("[%s] failed polling %s", self.name, self.TYPE)


  async def _pollStream(self, creatorPosts=True, retry=False):
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
      timestamp = parseDate(post['attributes']['published_at'])

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


  async def _pollMonocle(self, retry=False):
    resp = await self.http.get(MONOCLE_URL + self.monocle_id, params={
      'include': 'story',
      'fields[monocle-clip]': ','.join([
        'clip_type',
        'published_at',
        'thumbnail_url',
        'viewing_url',
      ]),
      'json-api-use-default-includes': 'false',
      'json-api-version': '1.0',
    })

    LOG.debug("[%s] fetched %s", self.name, resp.url)

    body = await resp.json(content_type='application/vnd.api+json')

    if 'included' not in body:
      return

    for post in body['included']:
      if post['type'] != 'monocle-clip':
        continue

      id = 'monocle.' + post['id']
      timestamp = parseDate(post['attributes']['published_at'])

      if await self.should_handle(id, timestamp):
        if not post['attributes']['viewing_url'] and not retry:
          raise InaccessiblePostError()

        LOG.info("[%s] announcing lens %s", self.name, str(id))

        message = convertLens(post)

        await self.discord.send(embed=message)
        await self.mark_handled(id, timestamp)
