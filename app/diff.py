#! /usr/bin/python
# -*- coding: utf-8 -*-
#
#  Copyright 2013 Fondazione Bruno Kessler
#  Author: <consonni@fbk.eu>
#  This work has been funded by Fondazione Bruno Kessler (Trento, Italy)
#  within the activities of the Digital Commons Lab
#
#  This file is part of wikipedia-tags-in-osm.
#  wikipedia-tags-in-osm is free software: you can redistribute it and/or
#  modify it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  wikipedia-tags-in-osm is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU General Public License
#  along with wikipedia-tags-in-osm.
#  If not, see <http://www.gnu.org/licenses/>.

import difflib
import re
from jinja2 import Markup


def get_difftable_difflib(old_text, new_text, pageid, section):
        dhtml = difflib.HtmlDiff()
        difftable = Markup(dhtml.make_table(fromlines=old_text.splitlines(),
                                            tolines=new_text.splitlines(),
                                            context=True
                                            )
                           )

        difftable = re.sub('nowrap="nowrap"', '', difftable)
        difftable = re.sub('&nbsp;', ' ', difftable)

        return difftable


def get_difftable_mediawiki(mwoauth, new_text, pageid, section):
        TABLE_WRAP = "<table>\n<tbody>{rows}\n</tbody>\n</table>"

        diff_query = {'action': 'query',
                      'titles': 'Project:Sandbox',
                      'prop': 'revisions',
                      'rvlimit': 1,
                      'rvdifftotext': new_text,
                      }

        if section:
            diff_query['rvsection'] = section

        diff_req = mwoauth.request(diff_query)

        revs = diff_req['query']['pages'][pageid]['revisions'][0]
        table_rows = revs['diff']['*']

        table_all = TABLE_WRAP.format(rows=table_rows)
        difftable = Markup(table_all)

        return difftable


if __name__ == '__main__':
    pass
