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

import re
from coords import coords_template

HEADING = re.compile(r'==[^=]+==')

COORD = re.compile('{{coord(.*)}}', re.IGNORECASE)


import ast
with open('../data/wikipedia/coords/templates_including_coords.txt',
          'r') as infile:
    TEMPLATES = [ast.literal_eval(t) for t in infile.readlines()]


def find_coords_templates(old_text):
    template = None

    coord = COORD.search(old_text)
    if coord:
        template = 'coord'
    else:
        for t in TEMPLATES:
            search_regex = '{{%s(.*)}}' % t['name']
            s = re.search(search_regex, old_text, re.IGNORECASE)

            if 'rifugio' in t['name'].lower():
                import pdb
                pdb.set_trace()

            if s:
                import pdb
                pdb.set_trace()

    return template


def get_new_text(lat, lon, dim, old_text='', template=None):
    new_text = old_text
    section = 0

    first_heading = HEADING.search(old_text)
    if first_heading:
        incipit = old_text[:first_heading.start()]

    if template:
        # do something
        pass

    else:
        tmpl = coords_template(lat=lat,
                               lon=lon,
                               dim=dim)
        if incipit:
            new_text = tmpl + '\n\n' + incipit
            old_text = incipit
            section = 0

        else:
            new_text = tmpl + '\n\n' + old_text
            section = -1

    return new_text, old_text, section


if __name__ == '__main__':
    with open('test/torre_pendente_di_pisa.txt', 'r') as infile:
        pisa = infile.read()

    with open('test/rifugio_laghi_gemelli.txt', 'r') as infile:
        rifugio = infile.read()

    find_coords_templates(rifugio)

    import pdb
    pdb.set_trace()
