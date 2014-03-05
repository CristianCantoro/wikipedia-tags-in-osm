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

import sys
import os

basedir = os.path.realpath(os.path.join(
    os.path.dirname(os.path.realpath(__file__)), '..'))

sys.path.append(basedir)

from utils import coords_deg2dms_cp, format_dms

BASE_TEMPLATE = "{{{{coord"\
                "|{lat_d:02d}|{lat_m:02d}|{lat_s:02d}|{lat_cp}"\
                "|{lon_d:02d}|{lon_m:02d}|{lon_s:02d}|{lon_cp}"\
                "{dim_str}"\
                "|display=title"\
                "|notes=<ref>Coordinate tratte da [[OpenStreetMap]]"\
                " ({links})</ref>"\
                "}}}}"

DIM_STR = "|dim:{}"

WIKILINK_TO_OSM = '[{osm_link} {osm_type} ID]'

OSM_LINK = 'http://www.openstreetmap.org/{osm_type}/{osm_id}'


def coords_template(lat, lon, osm_refs, dim=None):
    dms = format_dms(coords_deg2dms_cp(lat, lon))

    dim_str = ''
    if dim and dim > 0:
        dim_str = DIM_STR.format(dim)

    wikilinks = []
    for osm_type, osm_id in osm_refs:
        osm_link = OSM_LINK.format(osm_type=osm_type, osm_id=osm_id)
        link_wiki = WIKILINK_TO_OSM.format(osm_link=osm_link,
                                           osm_type=osm_type
                                           )
        wikilinks.append(link_wiki)

    return BASE_TEMPLATE.format(lat_d=dms['lat']['d'],
                                lat_m=dms['lat']['m'],
                                lat_s=dms['lat']['s'],
                                lat_cp=dms['lat']['cp'],
                                lon_d=dms['lon']['d'],
                                lon_m=dms['lon']['m'],
                                lon_s=dms['lon']['s'],
                                lon_cp=dms['lon']['cp'],
                                dim_str=dim_str,
                                links=', '.join(wikilinks)
                                )

if __name__ == '__main__':
    print
    print 'Coordinate di Berlino'
    print 'deg: (52.518611, 13.408056), dim=100'
    print 'atteso:'
    print '{{coord|52|31|07|N|13|24|29|E|dim:100|display=title' \
          '|notes=<ref>Coordinate tratte da [[OpenStreetMap]]' \
          ' ([http://www.openstreetmap.org/relation/1918 relation ID])' \
          '</ref>}}'
    print '---'
    print coords_template(52.518611, 13.408056, [('relation', 1918)], 100)
    print '==='
    print
    print 'Coordinate di Washington D.C.'
    print 'deg: (38.895111, -77.036667), dim=20'
    print 'atteso:'
    print '{{coord|38|53|42|N|77|02|12|W|dim:20|display=title' \
          '|notes=<ref>Coordinate tratte da [[OpenStreetMap]]' \
          ' ([http://www.openstreetmap.org/way/195523293 way ID])' \
          '</ref>}}'
    print '---'
    print coords_template(38.895111, -77.036667, [('way', 195523293)], 20)
    print '==='
    print
    print 'Coordinate di Santiago del Cile'
    print 'deg: (-33.437833, -70.650333)'
    print 'atteso:'
    print '{{coord|33|26|16|S|70|39|01|W|display=title' \
          '|notes=<ref>Coordinate tratte da [[OpenStreetMap]]' \
          ' ([http://www.openstreetmap.org/node/64776484 node ID])' \
          '</ref>}}'
    print '---'
    print coords_template(-33.437833, -70.650333, [('node', 64776484)])
    print '==='
    print
    print 'Coordinate di Washington D.C.'
    print 'deg: (38.895111, -77.036667), dim=20'
    print 'atteso:'
    print '{{coord|38|53|42|N|77|02|12|W|dim:20|display=title' \
          '|notes=<ref>Coordinate tratte da [[OpenStreetMap]]' \
          ' ([http://www.openstreetmap.org/way/195523293 way ID],' \
          ' [http://www.openstreetmap.org/node/64776484 node ID])' \
          '</ref>}}'
    print '---'
    print coords_template(38.895111,
                          -77.036667,
                          [('way', 195523293), ('node', 64776484)],
                          20
                          )
    print '==='
