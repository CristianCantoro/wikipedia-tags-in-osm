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
                "|display=title}}}}"

DIM_STR = "|dim:{}"


def coords_template(lat, lon, dim=None):
    dms = format_dms(coords_deg2dms_cp(lat, lon))

    dim_str = ''
    if dim and dim > 0:
        dim_str = DIM_STR.format(dim)

    return BASE_TEMPLATE.format(lat_d=dms['lat']['d'],
                                lat_m=dms['lat']['m'],
                                lat_s=dms['lat']['s'],
                                lat_cp=dms['lat']['cp'],
                                lon_d=dms['lon']['d'],
                                lon_m=dms['lon']['m'],
                                lon_s=dms['lon']['s'],
                                lon_cp=dms['lon']['cp'],
                                dim_str=dim_str
                                )

if __name__ == '__main__':
    print
    print 'Coordinate di Berlino'
    print 'deg: (52.518611, 13.408056), dim=100'
    print 'atteso:\n{{coord|52|31|07|N|13|24|29|E|dim:100|display=title}}'
    print '---'
    print coords_template(52.518611, 13.408056, 100)
    print '==='
    print
    print 'Coordinate di Washington D.C.'
    print 'deg: (38.895111, -77.036667), dim=20'
    print 'atteso:\n{{coord|38|53|42|N|77|02|12|W|dim:20|display=title}}'
    print '---'
    print coords_template(38.895111, -77.036667, 20)
    print '==='
    print
    print 'Coordinate di Santiago del Cile'
    print 'deg: (-33.437833, -70.650333)'
    print 'atteso:\n{{coord|33|26|16|S|70|39|01|W|display=title}}'
    print '---'
    print coords_template(-33.437833, -70.650333)
    print '==='
