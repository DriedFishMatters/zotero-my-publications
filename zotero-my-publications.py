#!/usr/bin/python3

"""zotero-my-publications.py

    Downloads bibliographic details from the Zotero "My Publications" collection
    and outputs formatted HTML, using the Zotero API.

    See the accompanying README file for details.

    Copyright 2020, Eric Thrift

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""

# Zotero user ID -- look under API keys in user settings to find this
USER_ID = ''
# Zotero username, as used on the profile page: http://zotero.org/<username>
USERNAME = ''
# Human readable version of your name
USER_DISPLAY_NAME = ''
# URL for your logo or portrait
LOGO = ''
# Link to your institutional or personal website, applied to the logo/portrait
URL= ''
# Output file (absolute path recommended)
TARGET_FILE = 'publications.html'

# Template for HTML output
TEMPLATE = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" integrity="sha384-JcKb8q3iqJ61gNV9KGb8thSsNjpSL0n8PARn9HuZOnIxN0hoP+VmmDGMN5t9UJ0Z" crossorigin="anonymous">
    <title>{USER_NAME}Publications</title>
  </head>
  <body style="background:#eee">
      <div class="container p-5 my-4 bg-white">
      <header><a href="{URL}"><img src="{LOGO}"></a></header>
      <h1 class="text-center display-3">Publications</h1>
      </div>
      <footer class="footer my-4">
      <div class="container">
        <p class="text-muted"><span>Generated from the <a href="http://zotero.org">Zotero</a> public library for <a href="http://zotero.org/{USERNAME}">{USERNAME}</a>.</span></p>
      </div>
    </footer>
  </body>
</html>
""".format(USER_NAME=USER_DISPLAY_NAME, LOGO=LOGO, URL=URL, USERNAME=USERNAME)

### -- END CONFIGURATION -- ###

import json
import datetime

from pyzotero import zotero
import bs4

zot = zotero.Zotero(USER_ID, 'user')

zot.add_parameters(
            itemType='-attachment',
            include='bib,data',
            style='chicago-author-date',
            linkwrap='0',
            sort='date',
            direction='desc'
        )

items = zot.everything(zot.publications())
item_types = zot.item_types()
item_types_dict = dict()
for type in item_types:
    item_types_dict[type['itemType']] = type['localized']

out = bs4.BeautifulSoup(TEMPLATE, 'html.parser')

for item in items:
    bib = bs4.BeautifulSoup(item['bib'], 'html.parser')

    bib.div.div.unwrap() # remove the bibliography wrapper
    bib.div.name = 'p' # change citation container from "div" to "p"
    del bib.p['style'] # remove hard-coded hanging indent

    if item['meta'].get('numChildren', 0) > 0:
        attachments = zot.children(item['key'])
        for a in attachments:
            button = bib.new_tag('a')
            if a['data']['url']:
                button['href'] = a['data']['url']
            else:
                # api should give "links.enclosure.href" but this is absent?
                button['href'] = a['links']['self']['href'] + '/file/view'
            button.string = '[{}]'.format(a['data']['title'])
            bib.p.append(button)

    abstract = item['data'].get('abstractNote')
    if abstract:
        abs = bib.new_tag('blockquote')
        abs['class'] = 'mx-3'
        abs.string = abstract
        bib.p.append(abs)

    itemType = item['data']['itemType']
    i = out.find(id=itemType)
    if not i:
        section = out.new_tag('section', id=itemType)
        h2 = out.new_tag('h2')
        h2.string=item_types_dict[itemType]
        section.append(h2)
        section.append(bib)
        out.html.body.div.append(section)
    else:
        i.append(bib)

# Add a document generation timestamp
now = datetime.datetime.now()
datespan = out.new_tag('span')
datespan.string = 'Updated {}'.format(now.strftime("%Y-%m-%d"))
out.html.body.footer.div.p.append(datespan)

with open(TARGET_FILE, 'wb') as pub:
    pub.write(out.prettify('utf-8'))
