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

import os
import urllib
import ConfigParser as configparser
from flask import Flask
from flask import render_template
from flask import request
from flask import redirect
from flask_mwoauth import MWOAuth
from jinja2 import Environment
from jinja2 import Markup
import difflib

from coords import coords_template

app = Flask(__name__)

app.config.update(
    DEBUG=True,
    PROPAGATE_EXCEPTIONS=True
)

BASEDIR = os.path.dirname(os.path.realpath(__file__))
CONFIG_FILENAME = 'keys.cfg'
CONFIG_FILE = os.path.realpath(
    os.path.join('..', 'wtosm', 'keys.cfg'))

config = configparser.ConfigParser()
config.read(CONFIG_FILE)

# print CONFIG_FILE

consumer_key = config.get('keys', 'consumer_key')
consumer_secret = config.get('keys', 'consumer_secret')

mwoauth = MWOAuth(consumer_key=consumer_key, consumer_secret=consumer_secret)
app.register_blueprint(mwoauth.bp)

app.jinja_env.filters['unquote'] = urllib.unquote


@app.route("/")
def index():
    username = repr(mwoauth.get_current_user(False))
    return "logged in as: " + username + "<br />" + \
           "pippo 5<br />" + \
           '<a href="login">login</a> / <a href="logout">logout</a>'


@app.route("/map")
def show_map():
    lat = float(request.args.get('lat', ''))
    lon = float(request.args.get('lon', ''))
    title = urllib.quote(request.args.get('title', ''))
    dim = int(request.args.get('dim', ''))

    return render_template('wikimap.html',
                           lat=lat,
                           lon=lon,
                           title=title,
                           dim=dim)


def _get_difftable_difflib(token_req, pageid, tmpl):
        revs = token_req['query']['pages'][pageid]['revisions'][0]
        old_text = revs['*']
        new_text = tmpl + '\n\n' + old_text

        dhtml = difflib.HtmlDiff()
        difftable = Markup(dhtml.make_table(old_text.splitlines(),
                                            new_text.splitlines()
                                            )
                           )
        return difftable


def _get_difftable_mediawiki(token_req, pageid, tmpl):
        TABLE_WRAP = "<table>\n<tbody>{rows}\n</tbody>\n</table>"

        revs = token_req['query']['pages'][pageid]['revisions'][0]
        old_text = revs['*']
        new_text = tmpl + '\n\n' + old_text

        diff_req = mwoauth.request({'action': 'query',
                                    'titles': 'Project:Sandbox',
                                    'prop': 'revisions',
                                    'rvlimit': 1,
                                    'rvdifftotext': new_text,
                                    })

        revs = diff_req['query']['pages'][pageid]['revisions'][0]
        table_rows = revs['diff']['*']

        table_all = TABLE_WRAP.format(rows=table_rows)
        difftable = Markup(table_all)

        return difftable


@app.route("/preview")
def preview():
    lat = float(request.args.get('lat', ''))
    lon = float(request.args.get('lon', ''))
    title = urllib.quote(request.args.get('title', ''))
    dim = int(request.args.get('dim', ''))

    next_url = 'preview?lat={lat}&lon={lon}&dim={dim}&title={title}'.format(
        lat=lat,
        lon=lon,
        dim=dim,
        title=title)

    next_url = urllib.quote_plus(next_url)

    if mwoauth.get_current_user(False) is None:
        return redirect('../app/login?next={next}'.format(next=next_url))
    else:
        token_req = mwoauth.request({'action': 'query',
                                     'titles': 'Project:Sandbox',
                                     'prop': 'info|revisions',
                                     'rvprop': 'timestamp|user'
                                               '|comment|content',
                                     'rvlimit': 1,
                                     'intoken': 'edit'
                                     })

        pageid = token_req['query']['pages'].keys()[0]

        token = token_req['query']['pages'][pageid]['edittoken']

        tmpl = coords_template(lat=lat,
                               lon=lon,
                               dim=dim)

        difftable = _get_difftable_mediawiki(token_req, pageid, tmpl)

        return render_template('preview.html',
                               difftable=difftable,
                               title=title
                               )


@app.route("/edit")
def edit():
    title = urllib.quote(request.args.get('title', ''))

    if mwoauth.get_current_user(False) is None:
        return 'Something went wrong, you are not logged in'
    else:
        # test = mwoauth.request({'action': 'edit',
        #                         'title': 'Project:Sandbox',
        #                         'summary': 'test summary',
        #                         'text': 'article content',
        #                         'token': token})
        return 'Well done!'


@app.route("/test")
def insert():

    token_req = mwoauth.request({'action': 'query',
                                 'titles': 'Project:Sandbox',
                                 'prop': 'info',
                                 'intoken': 'edit'
                                 })

    pageid = token_req['query']['pages'].keys()[0]

    token = token_req['query']['pages'][pageid]['edittoken']

    test = mwoauth.request({'action': 'edit',
                            'title': 'Project:Sandbox',
                            'summary': 'test summary',
                            'text': 'article content',
                            'token': token})

    return "Done!"

if __name__ == "__main__":
    from werkzeug.wsgi import DispatcherMiddleware
    from flask import redirect
    from flask import send_from_directory

    app.secret_key = "local secret is secret"

    @app.route('/css/<path:filename>')
    def serve_css(filename):
        return send_from_directory('css', filename)

    @app.route('/js/<path:filename>')
    def serve_js(filename):
        return send_from_directory('js', filename)

    @app.route('/lib/<path:filename>')
    def serve_lib(filename):
        return send_from_directory('lib', filename)

    @app.route('/img/<path:filename>')
    def serve_img(filename):
        return send_from_directory('img', filename)

    redirect_app = Flask(__name__)

    @redirect_app.route('/')
    @redirect_app.route('/app')
    def app_index():
        return redirect('/app/')

    base_app = Flask(__name__)

    base_app.config.update(
        DEBUG=True,
        PROPAGATE_EXCEPTIONS=True
    )

    base_app.wsgi_app = DispatcherMiddleware(redirect_app, {
        '/app':     app
    })

    base_app.run(host='localhost',
                 port=5000,
                 debug=True,
                 )
