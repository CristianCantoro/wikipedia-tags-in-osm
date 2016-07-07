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
import itertools as it
import wikipedia_template_parser as wtp
from coords import coords_template
from utils import coords_deg2dms_cp, format_dms

HEADING = re.compile(r'==[^=]+==')

COORD = re.compile(r'\{\{coord[^{}]*?', re.IGNORECASE)

CLOSE_TEMPLATE_COORDS = re.compile(r'[^{}]*?(\}\})?}}')

CLOSE_TEMPLATE = re.compile(r'[^{}]*?(\}\})?')

REF = re.compile(r'<ref>', re.IGNORECASE)

REFERENCES = re.compile(r'(\{\{|<)\s*references[^}>]*(\}\}|>)', re.IGNORECASE)

REFERENCES_SECTION = "== Note ==\n<references />\n\n"

# section regexes
NOTEREGEX = re.compile(r"==\s*note\s*==", flags=re.IGNORECASE)
BIBLIOREGEX = re.compile(r"==\s*bibliografia\s*==", flags=re.IGNORECASE)
CORRELSEZREGEX = re.compile(r"==\s*voci\s*correlate\s*==", flags=re.IGNORECASE)
OTHERPROJREGEX = re.compile(r"==\s*altri\s*progetti\s*==", flags=re.IGNORECASE)
LINKREGEX = re.compile(r"==\s*collegamenti esterni\s*==", flags=re.IGNORECASE)
EXTLINKREGEX = re.compile(r"\[http://(.*)\](.*)\n", flags=re.IGNORECASE)
PORTALREGEX = re.compile(r"{{portale\|(.*)}}", flags=re.IGNORECASE)
CATREGEX = re.compile(r"\[\[Categoria:(.*)\]\]", flags=re.IGNORECASE)
INTERPROGREGEX = re.compile(r"{{interprogetto(.*)}}\n", flags=re.IGNORECASE)

REGEXES = [NOTEREGEX, BIBLIOREGEX, CORRELSEZREGEX, OTHERPROJREGEX, LINKREGEX,
           EXTLINKREGEX, PORTALREGEX, CATREGEX, INTERPROGREGEX]


import ast
with open('../data/wikipedia/coords/templates_including_coords.txt',
          'r') as infile:
    TEMPLATES = [ast.literal_eval(t) for t in infile.readlines()]


def find_coords_templates(old_text):
    template_found = {}
    old_coords = None

    coord = COORD.search(old_text)
    if coord:
        template_found['name'] = 'coord'
        template_found['has_coords'] = True
        templates = wtp.data_from_templates(page='',
                                            lang='',
                                            wikitext=old_text
                                            )
        tmpl = [template['data']
                for template in templates
                if template['name'].lower() == 'coord'
                ]
        old_coords = tmpl and tmpl[0] or None

    else:
        for t in TEMPLATES:
            search_regex = r'{{%s(.*)' % t['name']
            match = re.search(search_regex, old_text, re.IGNORECASE)

            if match:
                templates = wtp.data_from_templates(page='',
                                                    lang='',
                                                    wikitext=old_text
                                                    )
                tmpl = [template['data']
                        for template in templates
                        if template['name'].lower() == t['name'].lower()
                        ]
                data = tmpl and tmpl[0] or None

                template_found['name'] = t['name']
                template_found['has_coords'] = False

                old_coords = {}
                for par in t['parameters']:
                    if data and par in data:
                        if data[par]:
                            template_found['has_coords'] = True

                            par_value, par_name = get_parameter(
                                par,
                                float(data[par]),
                                float(data[par]))

                            old_coords[par_name] = par_value

    if template_found and template_found['has_coords']:
        if old_coords:
            template_found['old_coords'] = old_coords
        else:
            template_found['old_coords'] = {'lat': None, 'lon': None}

    return template_found


def __find_reference_position(old_text):

    ref_pos = len(old_text)

    match = None
    for regex in REGEXES:
        match = regex.search(old_text)
        if match:
            ref_pos = match.start()
            break

    return ref_pos


def __add_newline(text, ref_pos):
    if len(text) > 0 and ref_pos > 0:
        if not text[ref_pos-1] == u'\n':
            text = text[:ref_pos] + '\n' + text[ref_pos:]

    return text


def get_new_text_no_template(lat,
                             lon,
                             osm_refs,
                             dim,
                             old_text=''
                             ):
    new_text = old_text
    references = REFERENCES.search(old_text)
    if references:
        section = 0
    else:
        section = -1

    first_heading = HEADING.search(old_text)

    tmpl = coords_template(lat=lat,
                           lon=lon,
                           osm_refs=osm_refs,
                           dim=dim
                           )

    if first_heading:
        start_heading = first_heading.start()
        incipit = old_text[:start_heading]
        new_text = tmpl + '\n\n' + incipit
        if not references:
            section = -1
            ref_pos = __find_reference_position(old_text)
            old_text = __add_newline(old_text, ref_pos)
            new_text += old_text[start_heading:ref_pos] + \
                REFERENCES_SECTION + \
                old_text[ref_pos:]

        else:
            old_text = incipit
            section = 0
    else:
        new_text = tmpl + '\n\n' + old_text
        section = -1
        if not references:
            ref_pos = __find_reference_position(new_text)
            new_text = new_text[:ref_pos] + \
                REFERENCES_SECTION + \
                new_text[ref_pos:]
            new_text = __add_newline(new_text, ref_pos)

    return new_text, old_text, section


def _get_element(name):
    ELEMENTS = {"_d": 'dec',
                "gradi": 'd',
                "minuti": 'm',
                "secondi": 's',
                "ns": 'cp',
                "ew": 'cp',
                "verso": 'cp'
                }

    el = 'dec'
    for k in ELEMENTS.keys():
        if k in name:
            el = ELEMENTS[k]
            break

    return el


def get_parameter(name, lat, lon):

    dms = coords_deg2dms_cp(lat, lon)
    dms = format_dms(dms)

    name = name.lower()
    if 'lat' in name:
        el = _get_element(name)

        if el == 'dec':
            return str(lat), 'lat'
        else:
            return str(dms['lat'][el]), 'lat'

    elif ('lon' in name) or ('lng' in name):
        el = _get_element(name)

        if el == 'dec':
            return str(lon), 'lon'
        else:
            return str(dms['lon'][el]), 'lon'
    else:
        return "Caso inatteso, non salvare questa pagina e segnalalo "\
               "agli sviluppatori. Grazie.", None


def __find_sections_intervals(text):

    headings_matches = HEADING.finditer(text)
    headings = [(h.start(), h.end()) for h in headings_matches]
    intervals = sum(headings, ())
    intervals = (0,) + intervals[::2] + (len(text),)
    section_intervals = [i for i
                         in enumerate([r for r
                                       in it.izip_longest(intervals[::],
                                                          intervals[1::],
                                                          fillvalue=0)
                                       ])]

    return section_intervals


def find_section(text, start_template, end_template):

    section_intervals = __find_sections_intervals(text)

    sections = [i[0] for i in section_intervals
                if start_template >= i[1][0] and end_template <= i[1][1]]

    section_number = -1
    if sections:
        section_number = sections[0]

    return section_number


def get_section_text(text, section_number):

    section_start = 0
    section_end = len(text)

    section_intervals = __find_sections_intervals(text)

    section_limits = [i[1] for i in section_intervals
                      if i[0] == section_number]

    if section_number != -1 and len(section_limits) == 1:
        section_start, section_end = section_limits[0]

    return text[section_start:section_end]


def get_new_text_with_template(lat,
                               lon,
                               osm_refs,
                               dim,
                               template,
                               old_text=''
                               ):

    references = REFERENCES.search(old_text)
    if references:
        section = 0
    else:
        section = -1

    if template['name'] == 'coord':
        coord = COORD.search(old_text)

        start_template = coord.start()

        end_parameter = coord.end()

        match_close = CLOSE_TEMPLATE_COORDS.search(old_text[end_parameter:],
                                                   re.MULTILINE
                                                   )
        end_template = end_parameter + match_close.end()

        new_template = coords_template(lat=lat,
                                       lon=lon,
                                       osm_refs=osm_refs,
                                       dim=dim
                                       )

        new_text = old_text[:start_template] + new_template + \
            old_text[end_template:]

    else:
        new_template_text = ''

        search_regex = r'{{%s(.*)' % template['name']
        match_template = re.search(search_regex, old_text, re.IGNORECASE)

        # template starts after parentesis and name
        start_template = match_template.start()
        start_template_data = match_template.start() + 2 + \
            len(template['name'])

        coord_params = [t['parameters']
                        for t in TEMPLATES
                        if t['name'].lower() == template['name'].lower()
                        ][0]

        templates = wtp.data_from_templates(page='',
                                            lang='',
                                            wikitext=old_text
                                            )
        tmpl = [t['data']
                for t in templates
                if t['name'].lower() == template['name'].lower()
                ]

        data = tmpl and tmpl[0] or None

        max_parameter = 0
        for k in data.keys():
            search_parameter = r'%s\s*=\s*' % k
            match_parameter = re.search(search_parameter,
                                        old_text[start_template_data:],
                                        re.IGNORECASE
                                        )
            end_parameter = match_parameter.end()
            if end_parameter > max_parameter:
                max_parameter = end_parameter

        end_last_parameter = start_template_data + max_parameter

        match_close = CLOSE_TEMPLATE.search(old_text[end_last_parameter:],
                                            re.IGNORECASE
                                            )

        if match_close:
            end_template = end_last_parameter + match_close.end()
            new_template_text = old_text[start_template:end_template]

            if template['has_coords']:
                for p in coord_params:
                    search_parameter = r'%s\s*=\s*' % p
                    match_parameter = re.search(search_parameter,
                                                new_template_text,
                                                re.IGNORECASE
                                                )
                    parameter_end = match_parameter.end()

                    search_parameter = r'(.*)'
                    match_parameter = re.search(
                        search_parameter,
                        new_template_text[parameter_end:],
                        re.IGNORECASE)

                    line_end = match_parameter.end()

                    value_start = parameter_end
                    value_end = value_start + line_end

                    new_parameter, parameter_name = get_parameter(p, lat, lon)

                    new_template_text = new_template_text[:value_start] + \
                        new_parameter + \
                        new_template_text[value_end:]

                    new_text = old_text[:start_template] + \
                        new_template_text + old_text[end_template:]
            else:
                new_template_text = new_template_text[:-2]
                new_line = '|{par_name} = {par_value}\n'
                for p in coord_params:
                    par_value, parameter_name = get_parameter(p, lat, lon)
                    new_parameter = new_line.format(par_name=p,
                                                    par_value=par_value)
                    new_template_text += new_parameter

                new_template_text += '}}'

                new_text = old_text[:start_template] + \
                    new_template_text + old_text[end_template:]

    if not references and REF.search(new_text):
        ref_pos = __find_reference_position(new_text)
        new_text = new_text[:ref_pos] + \
            REFERENCES_SECTION + \
            new_text[ref_pos:]
        section = -1
        new_text = __add_newline(new_text, ref_pos)

    else:
        section = find_section(old_text, start_template, end_template)

    new_text = get_section_text(new_text, section)
    old_text = get_section_text(old_text, section)

    return new_text, old_text, section


def get_new_text(old_text, parameters, optional):
    template = find_coords_templates(old_text)

    if template:
        new_text, old_text, section = get_new_text_with_template(
            lat=parameters['lat'],
            lon=parameters['lon'],
            osm_refs=zip(parameters['osm_type'], parameters['osm_id']),
            dim=optional['dim'],
            old_text=old_text,
            template=template)

    else:
        new_text, old_text, section = get_new_text_no_template(
            lat=parameters['lat'],
            lon=parameters['lon'],
            osm_refs=zip(parameters['osm_type'], parameters['osm_id']),
            dim=optional['dim'],
            old_text=old_text)

    return template, new_text, old_text, section


def __test(in_, out_):

    with open(in_, 'r') as infile:
        wikitext = infile.read().decode('utf-8')

    parameters = {'lat': 45.990001,
                  'lon': 9.800001,
                  'osm_type': ['node'],
                  'osm_id': [64776484]
                  }

    optional = {'dim': 100}

    template, new_text, old_text, section = get_new_text(
        old_text=wikitext,
        parameters=parameters,
        optional=optional)

    d = difflib.HtmlDiff()
    diff = d.make_file(old_text.split('\n'), new_text.split('\n'))

    with codecs.open(out_, 'w+', 'utf-8') as outfile:
        outfile.writelines(diff)


if __name__ == '__main__':
    import difflib
    import codecs

    print 'Torre pendente di Pisa'
    __test(in_='test/torre_pendente_di_pisa.txt',
           out_='test/torre_pendente_di_pisa.html'
           )

    print 'Rifugio laghi gemelli'
    __test(in_='test/rifugio_laghi_gemelli.txt',
           out_='test/rifugio_laghi_gemelli.html'
           )

    print 'Diga di Pieve di Cadore'
    __test(in_='test/diga_di_pieve_di_cadore.txt',
           out_='test/diga_di_pieve_di_cadore.html'
           )

    print 'Ara della Regina'
    __test(in_='test/ara_della_regina.txt',
           out_='test/ara_della_regina.html'
           )

    print 'Palazzo Borromeo (Isola Bella)'
    __test(in_='test/palazzo_borromeo_isola_bella.txt',
           out_='test/palazzo_borromeo_isola_bella.html'
           )

    print 'Pian di Palma'
    __test(in_='test/pian_di_palma.txt',
           out_='test/pian_di_palma.html'
           )
