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
import async_timeout
import asyncio
from html2text import HTML2Text
import json
from textwrap import TextWrapper

api_stream = 'https://www.patreon.com/api/stream'
# test
#webhook = 'https://discordapp.com/api/webhooks/NO_KEY_FOR_YOU'
# prod
webhook = 'https://discordapp.com/api/webhooks/NO_KEY_FOR_YOU'

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
      'icon_url': 'https://c5.patreon.com/external/logo/downloads_logomark_color_on_coral.png',
    },
  }

  if (post['attributes']['image']):
    embed['thumbnail'] = {
      'url':    post['attributes']['image']['large_url'],
      'height': post['attributes']['image']['height'],
      'width':  post['attributes']['image']['width'],
    }

  return {
    'embeds': [embed],
  }

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
      'content',
      'embed',
      'image',
      'published_at',
      'post_type',
      'title',
      'url',
    ]),
    'fields[user]': ','.join([
      'image_url',
      'full_name',
      'url',
    ]),
    'page[cursor]': 'null',
    'filter[creator_id]': 136449,
    'filter[is_by_creator]': ('true' if creatorPosts else 'false'),
    'json-api-use-default-includes': 'false',
    'json-api-version': '1.0',
  }

cookies = {
  'session_id': 'NO_KEY_FOR_YOU',
}

async def main():
  async with aiohttp.ClientSession(cookies=cookies) as session:
    async with async_timeout.timeout(10):
      resp = await session.get(api_stream, params=params(creatorPosts=False))
    print(str(resp.url))

    body = await resp.json(content_type='application/vnd.api+json')

    post = body['data'][8]
    user = authorForPost(post, body['included'])
    message = convertPost(post, user)

    print(json.dumps(message, indent=2))

    print('*** sending webhook')
    async with async_timeout.timeout(10):
      resp = await session.post(webhook, json=message)
    print(resp.url)
    print(resp.status)
    print(await resp.text())



loop = asyncio.get_event_loop()
loop.run_until_complete(main())
