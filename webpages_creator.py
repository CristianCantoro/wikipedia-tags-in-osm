#! /usr/bin/python
# -*- coding: utf-8 -*-
#
#  Copyright 2013 Simone F. <groppo8@gmail.com>
#
#  This file is part of wikipedia-tags-in-osm.
#  wikipedia-tags-in-osm is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  wikipedia-tags-in-osm is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU General Public License
#  along with wikipedia-tags-in-osm.  If not, see <http://www.gnu.org/licenses/>.

"""Create webpages with the lists of Wikipedia categories and articles
"""

import os
import urllib
import json
from data_manager import Category, Article
from subprocess import call
from jinja2 import Environment, FileSystemLoader

OSM_TYPES = {
'n': 'node',
'w': 'way',
'r': 'relation'
}

### Helpers ############################################################
class Helpers:
    def progress_strings(self, item, mode):
        """Calculate tagging progress
        """
        number = item.progress[mode]["num"]
        progressString = item.progress[mode]["string"]
        if number == 0.0:
            classe = "done0"
        elif number == 1.0:
            classe = "done100"
        elif number <= 0.25:
            classe = "done025"
        elif number <= 0.50:
            classe = "done050"
        elif number <= 0.75:
            classe = "done075"
        else:
            classe = "done099"
        return classe, progressString

    def wikipedia_link(self, item):
        text = item.name.replace("_", " ")
        title = "Vedi %s: %s" % (item.typ.lower(), text.replace("\"", "&quot;"))
        cssClass = ' class="wikipedia_link"'
        link = self.url_to_link(item.wikipediaUrl, title, text, None, cssClass)
        return link

    def osm_ids_string_for_overpass(self, osmIds):
        """Return an OSM ids string used by Overpass
        """
        osmTypeAbbr = {"n": "node", "w": "way", "r": "relation"}
        osmIdsString = ""
        for osmId in osmIds:
            osmIdsString += '%s(%s);' % (osmTypeAbbr[osmId[0]], osmId[1:])
        return osmIdsString

    def overpass_query(self, item):
        if isinstance(item, Article):
            elementsString = self.osm_ids_string_for_overpass(item.osmIds)
        elif isinstance(item, Category):
            elementsString = self.osm_ids_string_for_overpass(item.allOsmIds)
        else:
            #wrongTags and badTags are not articles nor categories
            elementsString = self.osm_ids_string_for_overpass(item)
        query = '('
        query += elementsString
        query += ');'
        query += '(._;>;);'
        query += 'out meta qt;'
        return query

    def josm_link(self, mode, data, img):
        url = "http://localhost:8111/"
        if mode == "download":
            url += "import?url=http://overpass.osm.rambler.ru/cgi/interpreter?data=" + data
            title = "Scarica in JOSM"
        elif mode == "load_and_zoom":
            left = data[1] - 0.0005
            right = data[1] + 0.0005
            top = data[0] + 0.0005
            bottom = data[0] - 0.0005
            url += "load_and_zoom?left=%f&amp;right=%f&amp;top=%f&amp;bottom=%f" % tuple((left, right, top, bottom))
            title = "Zooma in JOSM vicino all'oggetto da taggare"
        link = self.url_to_link(url, title, None, img)
        return link

    def edit_link(self, data, img, zoom=17, editor='iD'):
        url = "http://www.openstreetmap.org/edit?"
        if editor == 'iD':
            url += 'editor=id'
        elif editor == 'Potlatch2':
            url += 'editor=potlatch2'
        url += '#map=%s/%s/%s' % (zoom, data[0], data[1])
        title = "Zooma col browser, editor %s, vicino all'oggetto da taggare" % editor
        link = self.url_to_link(url, title, title, img)
        return link

    def overpass_turbo_link(self, query, cssClass=""):
        url = 'http://overpass-turbo.eu/index.html?Q=%s&amp;R' % urllib.quote_plus(query)
        title = "Visualizza come mappa cliccabile, immagine... (Overpass Turbo)"
        img = "../img/Overpass-turbo.png"
        if cssClass != "":
            cssClass = ' class="%s"' % cssClass
        link = self.url_to_link(url, title, None, img, cssClass)
        return link

    def osm_ids_string(self, item):
        osmTypeAbbr = {"n": "node", "w": "way", "r": "relation"}
        links = {"nodes": [], "ways": [], "relations": []}
        if isinstance(item, Article):
            osmIds = item.osmIds
        else:
            #item == ids of wrongTags or badTags
            osmIds = item
        #create links to OSM web pages
        for osmId in osmIds:
            url = "http://www.openstreetmap.org/browse/%s/%s" % (osmTypeAbbr[osmId[0]], osmId[1:])
            link = self.url_to_link(url, "%s" % "Vedi pagina OSM", osmId[1:])
            links[osmTypeAbbr[osmId[0]] + "s"].append(link)
        osmIdsString = ""
        for osmType, linksList in links.iteritems():
            if len(linksList) > 0:
                if osmIdsString != "":
                    osmIdsString += "<br>"
                if isinstance(item, Article):
                    imgPath = "../img/"
                else:
                    imgPath = "./img/"
                img = '<img title="%s" src="%s%s.png">' % (osmType[:-1], imgPath, osmType)
                osmIdsString += "%s %s" % (img, ", ".join(linksList))
        if isinstance(item, Article):
            #put the string into a div
            osmDivId = item.ident
            osmIdsString = '<div id="%s" style="display:none"><br>%s</div>' % (osmDivId + '_div', osmIdsString)
        return links, osmIdsString

    def missing_template_link(self, article):
        img_title = "Sulla pagina Wikipedia manca il template coord"
        img_src = "../img/no_template.png"
        img_tag = '<img src="{src}" title="{title}"'\
                  ' class="articleLinkImg" />'.format(src=img_src, 
                                                      title=img_title)
        span_tag = '<span class="missing_template_alert" {{data}}>'\
                   '{img}</span>'.format(img=img_tag)

        if article.OSMcoords:
            lat = article.OSMcoords[0]
            lon = article.OSMcoords[1]
            dim = article.OSMdim
            wikipedia_title = urllib.quote_plus(article.name.encode("utf-8"))

            osm_ids = []
            osm_types = []
            for osm_id in article.osmIds:
                osm_types.append(OSM_TYPES[osm_id[0]])
                osm_ids.append(osm_id[1:])

            ref = u"./subpages/WTOSMSUBPAGENAME.html"

            a_tag = u'<a href="../app/map?'\
                     'lat={lat}'\
                     '&lon={lon}'\
                     '&dim={dim}'\
                     '&title={title}'\
                     '&ref={ref}'\
                     '&id={ident}"'\
                     ' id={ident}>'\
                     '{{span}}</a>'.format(lat=lat,
                                           lon=lon,
                                           dim=dim,
                                           ref=ref,
                                           ident=article.ident,
                                           title=wikipedia_title
                                           )

            osm_id_dump = json.dumps([int(o) for o in  osm_ids])
            osm_types_dump = json.dumps(osm_types)

            data = u'data-lat="{lat}" data-lon="{lon}" '\
                    'data-dim="{dim}" '\
                    'data-wikipedia="{title}" '\
                    'data-referrer="{ref}" '\
                    'data-id="{ident}" '\
                    'data-osmid={osm_id} '\
                    'data-osmtype={osm_type}'.format(lat=lat,
                                                     lon=lon,
                                                     dim=dim,
                                                     title=wikipedia_title,
                                                     ref=ref,
                                                     ident=article.ident,
                                                     osm_id=osm_id_dump,
                                                     osm_type=osm_types_dump
                                                     )

            span_tag = span_tag.format(data=data)
            link = a_tag.format(span=span_tag)

        else:
            span_tag = span_tag.format(data='')
            link = span_tag

        return link

    def add_tags_link(self, category):
        url = "http://toolserver.org/~kolossos/osm-add-tags/index.php?"
        url += "lang=it"
        url += "&amp;bbox=%s" % self.app.COUNTRYBBOX
        url += "&amp;cat=%s" % urllib.quote_plus(category.name.encode("utf-8"))
        url += "&amp;key=*&amp;value=*&amp;basedeep=10&amp;types=*&amp;request=Submit&amp;iwl=yes"
        title = "Cerca oggetti ed aggiungi tag (WIWOSM add-tags)"
        img = "../img/add-tags.png"
        link = self.url_to_link(url, title, None, img)
        return link

    def url_to_link(self, url, title, text, img=None, cssClass="", target=""):
        """Return a link from some parameters
        """
        if target is None:
            target = ""
        else:
            target = ' target="_blank"'
        if img is not None:
            textOrImg = '<img src="%s" class="articleLinkImg">' % img
        else:
            textOrImg = text
        code = '<a href="%s" title="%s"%s%s>%s</a>' % (url, title, target, cssClass, textOrImg)
        return code

    def tagged_article_links(self, app, article):
        """Create links for tagged article from OSM objects to various
           services
        """
        #WIWOSM link
        wiwosmUrl = "http://toolserver.org/~kolossos/openlayers/kml-on-ol-json3.php?lang=%s&amp;title=%s" % (app.WIKIPEDIALANG, article.name)
        wiwosmTitle = "Vedi mappa Wikipedia (WIWOSM)"
        wiwosmImg = "../img/wiwosm.png"
        wiwosmLink = self.url_to_link(wiwosmUrl, wiwosmTitle, None, wiwosmImg)

        #Show a div with OSM ids of the article
        #osm ids div
        osmLinks, osmIdsDiv = self.osm_ids_string(article)
        #link for showing the div
        osmUrl = "javascript:showHideDiv(\'%s\');" % (article.ident + '_div')
        osmLinkTitle = "Vedi pagina OSM"
        #check what kinds of OSM primitive are tagged and use the
        #right icon
        osmTypeAbbr = [osmType[0] for osmType in osmLinks if osmLinks[osmType] != []]
        osmLinkImg = "../img/osm_%s.png" % "".join(sorted(osmTypeAbbr))
        osmLink = self.url_to_link(osmUrl, osmLinkTitle, None, osmLinkImg, "", None)

        query = self.overpass_query(article)

        #JOSM remote control link
        img = "../img/josm.png"
        josmLink = self.josm_link("download", query, img)

        #Overpass Turbo link
        overpassTurboLink = self.overpass_turbo_link(query)

        code = '\n      %s ' % wiwosmLink
        code += '\n      %s ' % osmLink
        code += '\n      %s ' % josmLink
        code += '\n      %s' % overpassTurboLink
        if app.args.show_missing_templates and hasattr(article, "hasTemplate"):
            if not article.hasTemplate:
                code += '\n      %s' % self.missing_template_link(article)
        code += '\n      %s' % osmIdsDiv
        return code

    def non_tagged_article_links(self, app, article):
        """Create links to various services for an article not tagged in OSM yet
        """
        if hasattr(article, "wikipediaCoords"):
            #the article is not tagged but Wikipedia knows its coordinates
            img = "../img/josm_load_and_zoom.png"
            img_id = "../img/id.png"
            if article.wikipediaCoordsSource == 'Nuts4Nuts':
                img = "../img/josm_load_and_zoom_blue.png"
                img_id = "../img/id_blue.png"
            code = self.josm_link("load_and_zoom", article.wikipediaCoords,
                                  img)
            code += '\n      %s ' % self.edit_link(article.wikipediaCoords,
                                                   img_id)
        else:
            code = ""
        return code

    def header_needed(self, subitems, attributeName):
        """Return True or False if any subcategory has wikipediaCoordinates
           or misses Coord template. It is used to know if it is
           necessary to show headers in index tables
        """
        for subitem in subitems:
            if subitem.isMappable:
                if getattr(subitem, attributeName) > 0:
                    return True
        return False


### Webpages creator ###################################################
class Creator():
    def __init__(self, app):
        self.app = app
        #When selectNonMappable==True the cells of tables in webpages
        #can be clicked, to create list of non mappable articles
        #or categories that can be copied into the file ./data/wikipedia/non_mappable
        selectNonMappable = True if app.clickable_cells == "true" else False
        self.homepages = []
        #Create homepage
        modes = ["themes", "regions"]
        if app.args.show_link_to_wikipedia_coordinates:
            modes.append("map")
        for modeNumber, mode in enumerate(modes):
            self.homepages.append(Homepage(app, (modeNumber, mode)).code)

        #Create categories pages
        for theme in app.themes:
            for category in theme.categories:
                category.articles_html = ArticlesTable(app, category, selectNonMappable).code
                for subcategory in category.subcategories:
                    subcategory.html = CategoryTable(app, subcategory, selectNonMappable).code
                category.html = Subpage(app, "themes", "", category, selectNonMappable).code

        #Create regions pages
        for region in app.regions:
            region.html = Subpage(app, "regions", "_1", region, selectNonMappable).code

        #Create errors page
        print " - render errors page"
        errorsTemplate = self.env.get_template('errors.html')

        self.errorsHtml = errorsTemplate.render(app=self.app,
                                                root = '../',
                                                path = '/',
                                                filename = 'errors.html',
                                                helpers=helpers)
        self.errorsHtml = self.errorsHtml.replace('{{root}}', '../')

        #Create non_mappable page
        print " - render non_mappable page"
        nonMappableTemplate = self.env.get_template('non_mappable.html')

        self.nonMappableHtml = nonMappableTemplate.render(app=self.app,
                                                          root = '../',
                                                          path = '/',
                                                          filename = 'non_mappable.html',
                                                          helpers=helpers)

        #Save all HTML files
        self.save_html_files()

    def save_html_files(self):
        """Save webpages as html files
        """
        # homepage
        for i, homepage in enumerate(self.homepages):
            filename = "index.html"
            if i > 0:
                filename = "index_%d.html" % i
            self.save_file(self.homepages[i], filename)
        # categories pages
        for theme in self.app.themes:
            for category in theme.categories:
                categoryFile = os.path.join("subpages", "%s.html" % category.name)
                category.html = category.html.replace('WTOSMSUBPAGENAME', category.name)
                self.save_file(category.html, categoryFile)
        # regions pages
        for region in self.app.regions:
            regionFile = os.path.join("subpages", "%s.html" % region.name)
            region.html = region.html.replace('WTOSMSUBPAGENAME', region.name)
            self.save_file(region.html, regionFile)
        # errors page
        self.save_file(self.errorsHtml, "errors.html")
        if not self.app.args.nofx:
            call("firefox html/index.html", shell=True)

    def save_file(self, text, fileName):
        fileOut = open(os.path.join(self.app.HTMLDIR, fileName), "w")
        if isinstance(text, unicode):
            text = text.encode("utf-8")
        fileOut.write(text)
        fileOut.close()


### Homepage ###########################################################
class Homepage(Helpers):
    def __init__(self, app, modeInfo):
        """Homepage with two tabs: themes, regions
        """
        (modeNumber, mode) = modeInfo
        modesNames = ["Temi", "Regioni"]
        modesTitles = ["Visualizza categorie per tema",
                       "Visualizza categorie per regione"]
        if app.args.show_link_to_wikipedia_coordinates:
            modesNames.append("Mappa")
            modesTitles.append("Visualizza mappa con articoli da taggare")
        self.app = app
        code = '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" http://www.w3.org/TR/html4/loose.dtd>'
        #Head
        code += '\n<html>\n  <head>'
        code += '\n    <meta http-equiv="Content-type" content="text/html;charset=UTF-8">'
        code += '\n    <title>Articoli di Wikipedia mappabili in OSM</title>'
        if self.app.args.bitly:
            stylecss = "http://bit.ly/1brC3Kk"
        else:
            stylecss = os.path.join("css", "style.css")
        code += '\n    <link rel="stylesheet" type="text/css" href="%s">' % stylecss
        code += '\n    <script type="text/javascript" charset="utf-8">'
        code += '\n      function showHideDiv(elementid){'
        code += '\n        if (document.getElementById(elementid).style.display == "none"){'
        code += '\n            document.getElementById(elementid).style.display = "";'
        code += '\n            }'
        code += '\n        else {'
        code += '\n            document.getElementById(elementid).style.display = "none";'
        code += '\n            }'
        code += '\n        }'
        code += '\n    </script>'
        if app.args.show_link_to_wikipedia_coordinates:
            code += '\n    <link rel="stylesheet" href="http://cdn.leafletjs.com/leaflet-0.7/leaflet.css" />'
            code += '\n    <!--[if lte IE 8]><link rel="stylesheet" href="http://cdn.leafletjs.com/leaflet-0.7/leaflet.ie.css" /><![endif]-->'
            code += '\n    <script type="text/javascript" src="http://cdn.leafletjs.com/leaflet-0.7/leaflet.js"></script>'
            code += '\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">'
            code += '\n    <!-- MarkerCluster CSS and JS -->'
            code += '\n    <link rel="stylesheet" href="./css/style.css" />'
            code += '\n    <link rel="stylesheet" href="./css/MarkerCluster.css" />'
            code += '\n    <link rel="stylesheet" href="./css/MarkerCluster.Default.css" />'
            code += '\n    <!--[if lte IE 8]><link rel="stylesheet" href="../dist/MarkerCluster.Default.ie.css" /><![endif]-->'
            code += '\n    <script type="text/javascript"  src="js/leaflet.markercluster-src.js"></script>'
            code += '\n    <!-- Labelling CSS and JS -->'
            code += '\n    <link rel="stylesheet" href="./css/leaflet.label.css" />'
            code += '\n    <script type="text/javascript" src="./js/leaflet.label.js"></script>'
            code += '\n    <script type="text/javascript" src="./GeoJSON/coords.js"></script>'
        code += '\n  </head>'
        #Body
        code += '\n<body>'
        code += '\n  <div id="update_time">Aggiornamento: %s</div>' % self.app.UPDATETIME
        code += '\n  <div id="header">'
        code += '\n    <h1><a id="top"></a>Articoli Wikipedia mappabili in OSM</h1>'
        code += '\n    <p>Liste di articoli Wikipedia (IT) mappabili in OpenStreetMap, tramite il tag "<b><a href="http://wiki.openstreetmap.org/wiki/Wikipedia" target="_blank">wikipedia</a> = it:Titolo dell\'articolo</b>".</p>'
        code += '\n    <!-- Informations -->'
        code += '\n    <p><a id="description" href="javascript:showHideDiv(\'info\');"><img src="./img/info.png" class="infoImg"> Informazioni e conteggi</a> | <a href="errors.html" title="Visualizza tag sospetti">Tag sospetti</a></p>'
        #Info
        code += '\n    <div id="info" style="display:none">'
        if self.app.users != {}:
            code += self.users_table()
        code += self.stats_table()
        code += '\n      <h2></h2>'
        code += '\n      <ul>'
        code += '\n        <li>Gli oggetti taggati compaiono in Wikipedia <a href="http://toolserver.org/~kolossos/openlayers/kml-on-ol.php?lang=it&amp;uselang=de&amp;params=41.89_N_12.491944444444_E_region%3AIT_type%3Alandmark&amp;title=Colosseom&amp;zoom=18&amp;lat=41.89&amp;lon=12.49284&amp;layers=B00000FTTTF">su una mappa</a> (progetto <a href="http://wiki.openstreetmap.org/wiki/WIWOSM" target="_blank">WIWOSM</a>).</li>'
        code += '\n        <li>La presenza di questi tag migliora i risultati delle ricerche eseguite su www.openstreetmap.org (Nominatim).</li>'
        code += '\n      </ul>'
        code += '\n      <h2>Come</h2>'
        code += '\n      <ul>'
        code += '\n        <li>Aggiungere all\'oggetto in OSM il tag <b>"wikipedia=it:Titolo dell\'articolo"</b>, lasciando gli spazi tra le parole.<br>Basta <b>una sola lingua</b>, se l\'articolo è già taggato in una lingua straniera non occorre aggiungere quella italiana (vedi <a href="http://wiki.openstreetmap.org/wiki/Wikipedia" target="_blank"> eccezioni</a> sul Wiki di OSM).</li>'
        code += '\n      </ul>'
        code += '\n      <h2>Strumenti utili per aggiungere tag</h2>'
        code += '\n      <ul>'
        code += '\n        <li><a href="http://josm.openstreetmap.de/wiki/Help/Plugin/Wikipedia" target="_blank">Plugin Wikipedia</a> per <a href="http://wiki.openstreetmap.org/wiki/IT:JOSM" target="_blank">JOSM</a>.</li>'
        code += '\n        <li><a href="http://wiki.openstreetmap.org/wiki/JOSM/Plugins/RemoteControl/Add-tags" target="_blank">add-tags</a>, si può usare questo servizio anche cliccando sulle icone <img src="./img/add-tags.png"> presenti in queste pagine.'
        code += '\n      </ul>'
        code += '\n      <h2>Difetti nelle liste</h2>'
        code += '\n      <ul>'
        code += '\n        <li> Articoli o categorie <b>non mappabili</b>, ad es. "es. Dipinti nel Museo Tal Dei Tali", possono essere rimossi dalla pagina, se segnalati (vedi mail).</li>'
        code += '\n        <li> Può accadere che in una sottocategoria ricadano articoli non riguardanti il tema di partenza. Se questi sono mappabili vengono comunque mostrati in tabella.</li>'
        code += '\n        <li> Articoli o sottocategorie appartenenti a più categorie possono ripetersi più volte in una stessa pagina (i conteggi ne tengono conto).</li>'
        code += '\n      </ul>'
        code += '\n      <h2>Programma per generare le pagine</h2>'
        code += '\n      <p>Codice: <a href="https://github.com/simone-f/wikipedia-tags-in-osm" target="_blank">wikipedia-tags-in-osm %s</a> (GPLv3)\
<br>Autore: <a href="mailto:groppo8@gmail.com">Simone F.</a></p>' % self.app.version
        code += '\n      <p>Contributors: Luca Delucchi, Cristian Consonni</p>'
        code += '\n      <p><br>Riconoscimenti ed attribuzioni:</p>'
        code += '\n      <p>Servizi linkati da queste pagine: \
<a href="http://wiki.openstreetmap.org/wiki/WIWOSM">WIWOSM</a> (master, Kolossos), \
<a href="http://wiki.openstreetmap.org/wiki/JOSM/Plugins/RemoteControl/Add-tags" target="_blank">add-tags</a> (Kolossos), \
<a href="http://overpass-turbo.eu/" target="_blank">OverpassTurbo</a> (tyr.asd).</p>'
        code += '\n      <p>Servizi usati per creare le pagine: \
<a href="http://toolserver.org/%7Edaniel/WikiSense/CategoryIntersect.php" target="_blank">CatScan</a> (Duesentrieb), \
<a href="http://toolserver.org/~kolossos/wp-world/pg-dumps/wp-world/">Wikipedia coordinates</a> (Kolossos), \
<a href="http://nuts4nutsrecon.spaziodati.eu/">Nuts4Nuts</a>, \
<a href="http://tools.wmflabs.org/catscan2/quick_intersection.php">quick_intersection</a> (Magnus Manske).</p>'
        code += '\n      <p>Icone dei temi: <a href="https://github.com/mapbox/maki" target="_blank">Maki</a> (BSD)<br>'
        code += '\n      Stemmi regionali: <a href="http://www.araldicacivica.it" target="_blank">www.araldicacivica.it</a> (<a href="http://creativecommons.org/licenses/by-nc-nd/3.0/it/">CC BY-NC-ND 3.0</a>)<br>'
        code += '\n      Icone di nodi, way, relazioni ed Overpass Turbo da <a href="http://wiki.openstreetmap.org/">Wiki OSM</a>.</p>'
        code += '\n    </div>'
        #Tabs: themes|regions|map
        code += '\n    <div id="tabs">'
        code += '\n      <ul>'
        for n, modeName in enumerate(modesNames):
            tabid = ""
            filename = "./index"
            if n > 0:
                filename += "_%d" % n
            filename += ".html"
            if n == modeNumber:
                tabid = ' id ="selected"'
            code += '\n        <li%s><a title="%s" href="%s">%s</a></li>' % (tabid, modesTitles[n], filename, modeName)
        code += '\n       </ul>'
        code += '\n    </div>'
        code += '\n  </div>'
        code += '\n  <div id="content">'
        code += self.homepage_tab(mode).encode("utf-8")
        code += '\n  </div>'
        code += '\n</body>\n</html>'
        self.code = code

    def stats_table(self):
        """Return html code of a table with the numbers of tagged/non tagged
           articles of the first and the last 9 days
        """
        red = "#cc0000"
        green = "#00cc7a"
        modes = [("to do", "Da mappare"),
                 ("mapped", "Mappati"),
                 ("total", "Totali")]

        code = '\n      <table id="stats">'
        code += '\n        <tr>'
        code += '\n          <th>Articoli</th>'
        if len(self.app.dates) >= 11:
            dates = [self.app.dates[0]] + self.app.dates[-9:]
            days = [self.app.days[0]] + self.app.days[-9:]
        else:
            dates = self.app.dates
            days = self.app.days
        #dates
        for date in dates:
            code += '\n          <th>%s</th>' % date
        code += '\n        </tr>'
        for mode, description in modes:
            #first cell
            if mode == "total":
                code += '\n        <tr>'
                code += '\n          <th colspan="%d">Tag</th>' % (len(days) + 1)
                code += '\n        </tr>'
            code += '\n        <tr>'
            code += '\n          <td>%s</td>' % description
            #data
            for index, day in enumerate(days):
                value = int(day[mode])
                differenceStr = ""
                if index > 0:
                    previousValue = int(days[index - 1][mode])
                    difference = int(value) - previousValue
                    if difference != 0:
                        differenceStr = str(difference)
                        if difference > 0:
                            if mode == "to do":
                                color = red
                            else:
                                color = green
                            differenceStr = "+%s" % differenceStr
                        elif difference < 0:
                            if mode == "to do":
                                color = green
                            else:
                                color = red
                        differenceStr = ' <span style = "color: %s">(%s)</span>' % (color, differenceStr)
                code += '\n          <td>%s%s</td>' % (value, differenceStr)
            code += '\n        </tr>'
        code += '\n      </table>'
        return code

    def users_table(self):
        """Return html code of a table with the mappers which added
           tags from the previous run of the program
        """
        #users = [[user name, tags num], ...]
        users = sorted(self.app.users.items(), key=lambda x: x[1], reverse=True)
        code = '\n      <div id="usersdiv">'
        code += '\n      <table id="users">'
        code += '\n        <tr><th>Mapper</th><th>Tag</th></tr>'
        for user, tagsNumber in users:
            mapperLink = '<a href="http://www.openstreetmap.org/user/%s/">%s</a>' % (urllib.quote_plus(user.encode("utf-8")), user.encode("utf-8"))
            code += '\n        <tr><td>%s</td><td>%s</td></tr>' % (mapperLink, tagsNumber)
        code += '\n      </table>'
        code += '\n      </div>'
        return code

    def homepage_tab(self, mode):
        """Return html code of homepage tabs: themes and regions
        """
        #Main index table with icons of themes or regions
        if mode in ("themes", "regions"):
            if mode == "themes":
                items = self.app.themes
            else:
                items = self.app.regions
            code = self.main_index(items, mode)
            #Indexes with categories in each theme or region
            for itemIdx, item in enumerate(items):
                #Title
                linkTop = '<a href="#top">&#8593;</a>'
                itemImg = '<img src="./img/%s/%s.png" class="item_img">' % (mode, item.name.lower())
                itemTitle = '%s%s' % (itemImg, item.name.replace("_", " "))
                if mode == "regions":
                    itemTitle = '<a href="./subpages/%s.html" title="Visualizza pagina della regione">%s</a>' % (item.name, itemTitle)
                code += '\n\n    <h3>%s<a id="%s"></a>%s</h3>' % (linkTop, item.name, itemTitle)
                #index of categories with progress
                pageType = "home"
                if itemIdx == 0:
                    showProgressHeader = True
                else:
                    showProgressHeader = False
                code += '\n%s' % IndexOfCategories(self.app, item, mode, pageType, showProgressHeader).code
        elif mode == "map":
            intro = u'<b>Clicca</b> su un articolo per visitarne la pagina o mapparlo/taggarlo tramite il link per JOSM (coordinate da Wikipedia).<br>\
Se un articolo non è mappabile in OSM, ad es. il luogo in cui si è svolto un evento storico, segnalalo come tale, affinché venga rimosso (vedi "Informazioni e conteggi").'
            code = '\n    <div id="map_intro">'
            code += '\n      <p>%s</p>' % intro
            code += '\n    </div>'
            code += '\n    <div id="map"></div>'
            code += '\n   <script type="text/javascript" src="./js/map.js"></script>'
            code += '\n   <!-- <div class="overlay">Articoli da taggare: <script type="application/x-javascript">document.write(coords.features.length);</script></div> -->'
        return code

    def main_index(self, items, mode):
        """Return html code of a table with themes or regions, to be used
           as main index of the homepage
        """
        code = '\n    <table id="home_index">'
        code += '\n      <tr>'
        columns = 5
        rows = [items[i:i + columns] for i in range(0, len(items), columns)]
        for row in rows:
            code += '\n      <tr>'
            for item in row:
                iconFile = "./img/%s/%s.png" % (mode, item.name.lower())
                if os.path.isfile(os.path.join(self.app.HTMLDIR, iconFile)):
                    icon = '<img src="%s">' % iconFile
                else:
                    icon = ""
                code += '\n        <td><a href="#%s">%s%s</a></td>' % (item.name, icon, item.name.replace("_", " "))
            code += '\n      </tr>'
        code += '\n    </table>'
        return code


### Subpage ############################################################
class Subpage(Helpers):
    def __init__(self, app, mode, suffix, item, selectNonMappable):
        """A webpage with data about a main category or a region.
        """

        self.app = app
        code = '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" http://www.w3.org/TR/html4/loose.dtd>'
        code += '\n<html>\n    <head>'
        code += '\n        <meta http-equiv="Content-type" content="text/html;charset=UTF-8">'
        code += '\n        <title>%s</title>' % self.app.homePageTitle
        code += '\n        <link rel="stylesheet" type="text/css" href="../css/style.css">'
        code += '\n        <script type="text/javascript" src="//code.jquery.com/jquery-1.10.2.min.js"></script>'
        code += '\n        <script type="text/javascript" src="//cdn.leafletjs.com/leaflet-0.7.1/leaflet.js"></script>'
        code += '\n        <script>'
        code += '\n         $(document).ready(function(){});'
        code += '\n            function showHideNonMappable (elementid){'
        code += '\n                var cssclass = "table#" + elementid + " td.non_mappable";'
        code += '\n                if ($(cssclass).css("display") != "table-cell"){'
        code += '\n                    $(cssclass).css("display", "table-cell");}'
        code += '\n                else {'
        code += '\n                   $(cssclass).css("display", "none");}};'
        code += '\n        </script>'
        if selectNonMappable:
            code += '\n        <script type="text/javascript">'
            code += '\n          var nonMappableCategories = "";'
            code += '\n          var nonMappableArticles = "";'
            code += '\n          function getName(cellThatWasClicked){'
            code += '\n            name = decodeURIComponent(cellThatWasClicked.firstChild)'
            code += '\n            name = name.replace("http://it.wikipedia.org/wiki/","");'
            code += '\n            name = name.replace("_"," ");'
            code += '\n            if (name.substring(0,10) == "Categoria:"){'
            code += '\n                nonMappableCategories += "|" + name.replace("Categoria:","");'
            code += '\n               }'
            code += '\n            else {'
            code += '\n               nonMappableArticles += "|" + name;'
            code += '\n            }'
            code += '\n          document.getElementById("nonMappableCategories").innerHTML = nonMappableCategories;'
            code += '\n          document.getElementById("nonMappableArticles").innerHTML = nonMappableArticles;'
            code += '\n          cellThatWasClicked.style.backgroundColor = "#ffb2b2";'
            code += '\n          }'
            code += '\n        </script>'
        code += '\n        <script type="text/javascript" charset="utf-8">'
        code += '\n          function showHideDiv(elementid){'
        code += '\n            if (document.getElementById(elementid).style.display == "none"){'
        code += '\n                document.getElementById(elementid).style.display = "";'
        code += '\n                }'
        code += '\n            else {'
        code += '\n                  document.getElementById(elementid).style.display = "none";'
        code += '\n                  }'
        code += '\n          }'
        code += '\n        </script>'
        code += '\n        <script src="../app/js/wtosm.js" type="text/javascript"></script>'
        code += '\n        <script src="../app/js/app/preview.js" type="text/javascript"></script>'
        code += '\n    </head>'
        code += '\n<body>'
        code += '\n\n<!-- Header -->'
        code += '\n<div id="header">'
        code += '\n    <div id="go_to_home"><a href="../index%s.html">&#8592; Tutte le categorie</a></div>' % suffix
        code += '\n    <div id="update_time">'
        if mode == "themes":
            code += '      Aggiornamento articoli in categoria: %s<br>' % item.updateTime
        code += '\n      Aggiornamento stato mappatura: %s' % self.app.UPDATETIME
        code += '\n    </div>'
        code += '\n</div>'

        code += '\n\n<!-- Content -->'
        code += '\n<div id="content">'

        code += '\n<div id="app-popup-main" class="app-popup">'
        code += '\n  <a href="javascript:void(0)" class="close" id="close-button"></a>'
        code += '\n  <div id="app-popup-main-container" class="app-popup-container">Container</div>'
        code += '\n</div>'

        # Title. Main category or region name
        if mode == "themes":
            progressClass, progressString = self.progress_strings(item, "allMArticles")
            code += '\n<h2><a id="index"></a>%s (%s)</h2>' % (self.wikipedia_link(item), progressString)
        else:
            #mode == "regions"
            img = '<img src="../img/%s/%s.png" class="item_img">' % (mode, item.name.lower())
            code += '\n<h2>%s<a id="index"></a>%s</h2>' % (img, item.name.replace("_", " "))

        if selectNonMappable:
            code += '\n<div id="selectNonMappable">'
            code += '\n  Per contrassegnare alcune categorie ed articoli come "non mappabili": clicca sulle loro celle, copia le stringhe qui sotto ed incollale nel file "./data/wikipedia/non_mappable".<br><br>'
            code += '\n  Categorie:'
            code += '\n  <div id="nonMappableCategories">&nbsp;</div><br>'
            code += '\n  Articoli:'
            code += '\n  <div id="nonMappableArticles">&nbsp;</div>'
            code += '\n</div>'

        # Legenda
        code += '\n\n<!-- Legenda -->'
        code += '\n<p><a href="javascript:showHideDiv(\'legenda\');"><img src="../img/info.png" class="infoImg"> Legenda</a></p>'
        code += '\n<div id="legenda" style="display:none">'
        code += self.legend_table()

        # Index with articles and subcategories of a category
        code += '\n\n<!-- Index -->'
        if mode == "themes" and item.articles != [] and item.titles == []:
            code += '\n<div class="showHideNonMappable"><a href=\'javascript:showHideNonMappable("%s_index");\' title="Visualizza sottocategorie non mappabili">Mostra non mappabili</a></div>' % item.ident
        code += '\n%s' % IndexOfCategories(app, item, mode, pageType="sub").code

        # Articles table
        if item.articles != []:
            code += '\n\n<!-- Articles -->'
            articlesProgressString = ""
            if item.titles != []:
                articlesProgressClass, articlesProgressString = self.progress_strings(item, "articles")
            code += '\n\n<h3><a href="#index">&#8593;</a> <a id="Articles"></a>Articoli %s</h3>' % articlesProgressString
            divId = "%s_articles" % item.ident
            if not item.articlesAreAllMappable:
                code += '\n<div class="showHideNonMappable"><a href=\'javascript:showHideNonMappable("%s");\' title="Visualizza articoli non mappabili">Mostra non mappabili</a></div>' % divId
            code += '\n%s\n' % item.articles_html

        # Subcategories tables
        code += '\n\n<!-- Subcategories -->'
        for subcategory in item.subcategories:
            progressString = ""
            if subcategory.isMappable:
                progressClass, progressString = self.progress_strings(subcategory, "allMArticles")
            if subcategory.allTitlesInOSM != []:
                query = self.overpass_query(subcategory)
                overpassTurboLink = " %s" % self.overpass_turbo_link(query)
            else:
                overpassTurboLink = ""
            code += '\n\n<h3>'
            code += '<a href="#index">&#8593;</a> '
            code += '<a id="%s"></a>' % subcategory.name
            code += '%s <span class=%s>%s</span>' % (self.wikipedia_link(subcategory), progressClass, progressString)
            if not len(subcategory.allTitles) == len(subcategory.allTitlesInOSM):
                code += " %s" % self.add_tags_link(subcategory)
            code += '%s</h3>' % overpassTurboLink
            if not subcategory.isAllMappable:
                code += '\n<div class="showHideNonMappable"><a href="javascript:showHideNonMappable(\'%s\');" title="Mostra anche categorie ed articoli non mappabili">Mostra non mappabili</a></div>' % subcategory.ident
            code += '\n%s\n' % subcategory.html
        code += '\n</div>'
        code += '\n</body>\n</html>'
        self.code = code

    def legend_table(self):
        """Return an html table with the legend
        """
        code = '\n  <table id="legend">'
        code += '\n    <tr><td class="index_done100"></td><td>100% articoli taggati</td></tr>'
        code += '\n    <tr><td class="index_done099"></td><td>99% articoli taggati</td></tr>'
        code += '\n    <tr><td class="index_done075"></td><td>75% articoli taggati</td></tr>'
        code += '\n    <tr><td class="index_done050"></td><td>50% articoli taggati</td></tr>'
        code += '\n    <tr><td class="index_done025"></td><td>25% articoli taggati</td></tr>'
        code += '\n    <tr><td class="index_done0"></td><td>0% articoli taggati</td></tr>'
        code += '\n    <tr><td><img src="../img/add-tags.png"></td><td>Cerca in OSM possibili oggetti corrispondenti agli articoli e taggali facilmente tramite lo strumento <a href="http://wiki.openstreetmap.org/wiki/JOSM/Plugins/RemoteControl/Add-tags" target="_blank">add-tags</a></td></tr>'
        code += '\n    <tr><td><img src="../img/wiwosm.png"></td><td>Vedi l\'oggetto sulla mappa Wikipedia</td></tr>'
        code += '\n    <tr><td><img src="../img/josm.png"></td><td>Scarica l\'oggetto in JOSM</td></tr>'
        code += '\n    <tr><td><img src="../img/osm.png"></td><td>Vedi la pagina OSM dell\'oggetto</td></tr>'
        code += '\n    <tr><td><img src="../img/Overpass-turbo.png"></td><td>Vedi gli oggetti su Overpass Turbo (mappa cliccabile, esporta come immagine...)</td></tr>'
        code += '\n    <tr><td><img src="../img/no_template.png"></td><td>All\'articolo su Wikipedia manca il <a href="https://it.wikipedia.org/wiki/Template%3ACoord" target="_blank">template Coord</a>. Clicca su un\'icona per ulteriori informazioni</td></tr>'
        code += '\n    <tr><td nowrap><img src="../img/josm_load_and_zoom.png"><img src="../img/id.png"></td>'
        code += '\n      <td>L\'articolo non è taggato ma Wikipedia ne conosce la posizione. Clicca sull\'icona per zoomare con l\'editor JOSM / iD sulla posizione conosciuta e trovare più facilmente l\'oggetto da taggare</td>'
        code += '\n    </tr>'
        code += '\n    <tr><td nowrap><img src="../img/josm_load_and_zoom_blue.png"><img src="../img/id_blue.png"></td>'
        code += '\n      <td>L\'articolo non è taggato ma ne è stata calcolata la posizione approssimata tramite i contenuti dell\'articolo e <a href="https://github.com/SpazioDati/Nuts4Nuts" target="_blank">Nuts4Nuts</a>. Clicca sull\'icona per aprire JOSM alla posizione conosciuta e trovare più facilmente l\'oggetto da taggare</td>'
        code += '\n    </tr>'
        code += '\n  </table>'
        code += '\n</div>'
        return code.decode("utf-8")


class ArticlesTable(Helpers):
    def __init__(self, app, item, selectNonMappable):
        """Return an html table with articles of a category
        """
        self.app = app

        if item.articles == []:
            self.code = ""
            return

        tableId = ""
        if not item.articlesAreAllMappable:
            tableId = ' id="%s_articles"' % item.ident
        code = '\n<table class="data"%s>' % tableId
        articles = item.articles
        for article in articles:
            cssclass = ""
            colspan = ""
            if not article.isMappable:
                cssclass = ' class="non_mappable"'
                colspan = ' colspan="2"'
            else:
                if article.inOSM:
                    links = self.tagged_article_links(app, article)
                else:
                    links = self.non_tagged_article_links(app, article)
            code += "\n  <tr>"
            onclick = ""
            if selectNonMappable:
                onclick = ' onclick="getName(this);"'
            code += "\n    <td%s%s%s>%s</td>" % (onclick, cssclass, colspan, self.wikipedia_link(article))
            if article.isMappable:
                code += "\n    <td>%s</td>" % links
            code += "\n  </tr>"
        code += "\n</table>"
        self.code = code


class CategoryTable(Helpers):
    def __init__(self, app, category, selectNonMappable):
        """Return an html table with subcategories (and their articles)
           of a category
        """
        self.app = app
        self.selectNonMappable = selectNonMappable
        columnsNumber = self.table_columns_number(category) + 1
        tableId = ""
        if not category.isAllMappable:
            tableId = ' id="%s"' % category.ident
        code = '\n<table class="data"%s>' % tableId
        code += "\n  <tr>"
        code = self.build_table(code, category, columnsNumber)
        code += '\n</table>'
        self.code = code

    def table_columns_number(self, category, i=0):
        if category.subcategories != []:
            columnsNumber = max([self.table_columns_number(subcategory, i + 1) for subcategory in category.subcategories])
        else:
            columnsNumber = i
        return columnsNumber

    def build_table(self, code, category, columnsNumber, level=0):
        """Build table by recursively reading subcategories and articles
           of the category
        """
        articles = category.articles
        subcategories = category.subcategories
        isFirstItem = True
        #articles
        for article in articles:
            colspan = columnsNumber - level
            if not article.isMappable:
                colspan += 1
            if colspan > 1:
                colspan = " colspan=%s" % str(colspan)
            else:
                colspan = ""
            code += self.add_item(article, isFirstItem, colspan, "")
            isFirstItem = False
        #subcategories
        for subcategory in subcategories:
            rowsnumber = len(subcategory.allArticles)
            if rowsnumber > 1:
                rowspan = " rowspan=%s" % rowsnumber
            else:
                rowspan = ""
            code += self.add_item(subcategory, isFirstItem, "", rowspan)
            isFirstItem = False
            code = self.build_table(code, subcategory, columnsNumber, level + 1)
        return code

    def add_item(self, item, isFirstItem, colspan, rowspan):
        """Add a cell to the table
        """
        code = "\n  <tr>" if not isFirstItem else ""
        onclick = ""
        if self.selectNonMappable:
            onclick = ' onclick="getName(this);"'
        cssClasses = []
        if not item.isMappable:
            cssClasses.append("non_mappable")
        if isinstance(item, Category):
            cssClasses.append("category")
        if cssClasses == []:
            cssClass = ""
        else:
            cssClass = ' class="%s"' % " ".join(cssClasses)
        #Category
        if isinstance(item, Category):
            catData = self.wikipedia_link(item)
            if not len(item.allTitles) == len(item.allTitlesInOSM):
                #add a link to WIWOSM tool "add-tags"
                catData += "\n %s" % self.add_tags_link(item)
            if item.allTitlesInOSM != [] and not self.selectNonMappable:
                #add a link to overpass for showing all objects
                query = self.overpass_query(item)
                linkClass = "overpassTurboLink"
                catData += "\n %s" % self.overpass_turbo_link(query, linkClass)
            code += "\n    <td%s%s%s>%s</td>" % (onclick, rowspan, cssClass, catData)
        #Article
        if isinstance(item, Article):
            code += "\n    <td%s%s%s>%s</td>" % (onclick, colspan, cssClass, self.wikipedia_link(item))
            if item.isMappable:
                #add one more cell with article info (links if tagged)
                nowrap = ""
                if item.inOSM:
                    links = self.tagged_article_links(self.app, item)
                else:
                    links = self.non_tagged_article_links(self.app, item)
                if links != "":
                    nowrap = " NOWRAP"
                code += "\n    <td%s>%s</td>" % (nowrap, links)
            code += "\n  </tr>"
        return code

                #Article tagging status cell
                cell = {"attr": nowrap, "content": links}
                self.rows[-1].append(cell)


class Redirect():
    """Class to create the index.html to redirect to the preferred language"""
    def __init__(self, app, locale_langcode):
        print " - render redirect page to %s" % locale_langcode
        htmlFile = "redirect.html"
        self.app = app
        self.locale_langcode = locale_langcode
        self.env = Environment(extensions=['jinja2.ext.i18n',
                                           'jinja2.ext.autoescape'],
                               loader=FileSystemLoader("templates"),
                               trim_blocks=True,
                               lstrip_blocks=True)
        self.env.install_gettext_translations(self.app.translations)
        indexTemplate = self.env.get_template(htmlFile)
        code = indexTemplate.render(lang=locale_langcode)
        fileOut = open(os.path.join(self.app.HTMLDIR, 'index.html'), "w")

        if isinstance(code, unicode):
            code = code.encode("utf-8")
        fileOut.write(code)
        fileOut.close()
