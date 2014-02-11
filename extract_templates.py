#! /usr/bin/python
# -*- coding: utf-8 -*-

import requests
import wikipedia_template_parser as wtp
from lxml import etree
import re
import json


def templates_including_coords():
    LINKSCOORD = "http://it.wikipedia.org/w/index.php?title="\
                 "Speciale:PuntanoQui/Template:Coord&namespace=10&limit=500"

    req = requests.get(LINKSCOORD)

    templates = list()
    if req.ok:
        doc = etree.fromstring(req.text)
        tmpl_list = doc.xpath('//div[@id="mw-content-text"]//li/a')

        templates = [tmpl.text
                     for tmpl in tmpl_list
                     if not tmpl.text.lower().endswith('/man')
                     ]

    return templates


def get_parameters(template):
    try:
        data = wtp.data_from_templates(template+'/man', "it")
    except ValueError:
        return []

    try:
        tabella = [d for d in data
                   if data[0]['name'] == 'TabellaTemplate'][0]
    except IndexError:
        return []

    stringa_parametri = tabella['data']['parametri']
    parametri = [p.replace('{{', '').replace('}}', '').split('~')[1]
                 for p in re.findall("{{[^{}]+}}", stringa_parametri)
                 ]

    return parametri


def write(outfile, addfile=None):
    templates = templates_including_coords()

    twparslist = []
    for t in templates:
        parametri = get_parameters(t)
        twpars = {'name': t.replace('Template:', ''),
                  'parameters': [p for p in parametri
                                 if 'lat' in p.lower() or 'lon' in p.lower()]
                  }
        twparslist.append(twpars)

    # with open(args.outfile, 'wb') as output:
    #     # Pickle the list using the highest protocol available.
    #     pickle.dump(twpars, output, -1)

    addtwp = None
    if addfile is not None:
        addtwp = read(addfile)

        for t in addtwp:
            repeat = [(id_, tmp)
                      for (id_, tmp) in enumerate(twparslist)
                      if tmp['name'] == t['name']
                      ]
            if repeat:
                id_ = repeat[0][0]
                twparslist[id_] = t
                addtwp.remove(t)

        twparslist = twparslist + addtwp

    with open(outfile, 'w+') as out:
        for twp in twparslist:
            out.write('{}\n'.format(json.dumps(twp)))


def read(infile):
    with open(infile, 'r') as in_:
        twp = [json.loads(l.strip()) for l in in_.readlines()]

    return twp


def main():
    # Options
    text = 'Descrizione'

    parser = argparse.ArgumentParser(description=text)

    parser.add_argument("-f", "--file",
                        help='Nome del file di output con i dati '
                             '[default: '
                             './data/wikipedia'
                             '/coords/templates_with_coords.txt]',
                        default=os.path.join("data",
                                             "wikipedia",
                                             "coords",
                                             "templates_including_coords.txt"
                                             ),
                        action="store"
                        )
    parser.add_argument("-a", "--add",
                        help='Nome del file con una lista di template '
                             '(serve per aggiungere alcuni template "a mano" '
                             '[default: '
                             './data/wikipedia'
                             '/coords/add_templates_with_coords.txt]',
                        default=os.path.join("data",
                                             "wikipedia",
                                             "coords",
                                             "add_templates"
                                             "_including_coords.txt"
                                             ),
                        action="store"
                        )
    parser.add_argument("--no-add",
                        help="Non aggiungere la lista dei template",
                        dest='no_add',
                        action="store_true"
                        )
    parser.add_argument("-r", "--read",
                        help="leggi il file invece di scriverlo",
                        action="store_true"
                        )

    args = parser.parse_args()

    if args.read:
        read(args.file)
    else:
        if args.no_add:
            write(args.file)
        else:
            write(args.file, args.add)

if __name__ == '__main__':
    import argparse
    import os

    main()
