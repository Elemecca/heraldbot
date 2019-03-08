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

import datetime
import email.utils
from html.parser import HTMLParser
from html2text import HTML2Text
import re
import textwrap


def parse_3339(value):
  """parses an RFC 3339 / ISO 8601 date string"""
  # uses regexes to compensate for strptime's shortcomings

  # convert the `Z` timezone spec to `+0000`
  value = re.sub(r'Z$', '+0000', value)

  # strip all optional separators (colon, hyphen before T)
  value = re.sub(r':|-(?=.*T)', '', value)

  # add microseconds if missing
  value = re.sub(r'(?<!\.\d{6})(?=[+-])', '.000000', value)

  return datetime.datetime.strptime(value, '%Y%m%dT%H%M%S.%f%z')

def parse_2822(value):
  """parses an RFC 2822 (email, HTTP, RSS) date string"""
  return email.utils.parsedate_to_datetime(value)

def html_to_summary(text):
  """converts an HTML document to a short summary"""
  h2 = HTML2Text()
  h2.body_width = None
  h2.ignore_links = True
  h2.images_to_alt = True

  return textwrap.shorten(h2.handle(text), width=250)

def html_get_image(text):
  class ImageFetchParser(HTMLParser):
    image = None
    def handle_starttag(self, tag, attrs):
      if self.image is None and tag == 'img':
        src = next(iter([ a[1] for a in attrs if a[0] == 'src' ]))
        if src and '/tools/commentcount' not in src:
          self.image = src

  parser = ImageFetchParser()
  parser.feed(text)
  return parser.image
