#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Copyright 2013 Fondazione Bruno Kessler, 2016 Cristian Consonni
#  Author: Cristian Consonni <consonni@fbk.eu>
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
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask import abort
from flask import url_for
from flask import flash
from flask_mwoauth import MWOAuth
from urlparse import urlparse
import binascii
import HTMLParser
import json
import wikipedia_template_parser as wtp

from diff import get_difftable_difflib
from templates import get_new_text

app = Flask(__name__)

OSM_TYPES = ['node', 'way', 'relation']

BASEDIR = os.path.dirname(os.path.realpath(__file__))
CONFIG_FILENAME = 'settings.cfg'
CONFIG_FILE = os.path.realpath(
    os.path.join('..', 'wtosm', CONFIG_FILENAME))

# development settings
if os.environ.get('WTOSM_DEV', None) or __name__ == "__main__":
    CONFIG_FILENAME = 'settings.dev.cfg'
    CONFIG_FILE = os.path.realpath(
        os.path.join('..', 'wtosm', 'dev', CONFIG_FILENAME))
    app.config.update(
        DEBUG=True,
        PROPAGATE_EXCEPTIONS=True
    )

config = configparser.ConfigParser()
config.read(CONFIG_FILE)

# print CONFIG_FILE

consumer_key = config.get('keys', 'consumer_key')
consumer_secret = config.get('keys', 'consumer_secret')

mwoauth_mw = MWOAuth(base_url='https://it.wikipedia.org/w',
                     clean_url='https://it.wikipedia.org/wiki',
                     consumer_key=consumer_key,
                     consumer_secret=consumer_secret
                     )

# app.register_blueprint(mwoauth_mw.bp)

app.jinja_env.filters['unquote'] = urllib.unquote

app.jinja_env.filters['unescape'] = HTMLParser.HTMLParser().unescape

app.jinja_env.filters['jsondumps'] = json.dumps

templates_file = config.get('app', 'templates_file')

template_coords = []

try:
    from extract_templates import read
    template_coords = read(templates_file)
except:
    pass


def textarea_default_height(text):
    return len(text.split('\n')) + 5

app.jinja_env.globals['textarea_default_height'] = textarea_default_height


def generate_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = binascii.b2a_hex(os.urandom(24))
    return session['_csrf_token']

app.jinja_env.globals['csrf_token'] = generate_csrf_token


@app.route("/")
def index():
    username = mwoauth_mw.get_current_user(False)
    return render_template('index.html',
                           root='/',
                           username=username)

# code from flask-mwoauth
@app.route("/login")
def login():

    uri_params = {'oauth_consumer_key': mwoauth_mw.mwoauth.consumer_key}
    # import pdb
    # pdb.set_trace()
    redirector = mwoauth_mw.mwoauth.authorize(**uri_params)

    if 'next' in request.args:
        oauth_token = session[mwoauth_mw.mwoauth.name + '_oauthtok'][0]
        session[oauth_token + '_target'] = request.args['next']

    return redirector

@app.route("/login/success")
def login_success():
    username = mwoauth_mw.get_current_user(False)
    return render_template('loginsuccess.html',
                           username=username
                           )


@app.route('/logout')
def logout():
    username = session['username']
    session['mwo_token'] = None
    session['username'] = None
    if 'next' in request.args:
        return redirect(request.args['next'])
    return render_template('logout.html',
                           username=username
                           )

# code from flask-mwoauth
@app.route("/oauth-callback")
def oauth_authorized():
    resp = mwoauth_mw.mwoauth.authorized_response()
    next_url_key = request.args['oauth_token'] + '_target'
    default_url = url_for(mwoauth_mw.default_return_to)

    next_url = session.pop(next_url_key, default_url)

    if resp is None:
        flash(u'You denied the request to sign in.')
        return redirect(next_url)
    session['mwo_token'] = (
        resp['oauth_token'],
        resp['oauth_token_secret']
    )

    username = mwoauth_mw.get_current_user(False)
    flash('You were signed in, %s!' % username)

    return redirect(next_url)


def validate_parameters(args):

    try:
        lat = float(args.get('lat', ''))
    except ValueError:
        lat = None

    try:
        lon = float(args.get('lon', ''))
    except ValueError:
        lon = None

    osm_id = args.get('osm_id', '')
    osm_ids = osm_id.split(',')

    osm_ids_num = []
    try:
        for oid in osm_ids:
            osm_ids_num.append(int(oid))
    except ValueError:
            osm_ids_num = None

    osm_type = args.get('osm_type', '')
    osm_types = osm_type.split(',')

    osm_types_norm = []
    for otype in osm_types:
        if otype in OSM_TYPES:
            osm_types_norm.append(otype)
        else:
            osm_types_norm = None
            break

    title = args.get('title', '')

    dim = int(args.get('dim', 0))
    referrer = args.get('ref', '')
    id_ = args.get('id', '')

    error = 0
    if not (lat and lon and title and osm_ids_num and osm_types_norm):
        error = 1
        parameters = {'lat': "La latitudine dell'oggetto",
                      'lon': "La longitudine dell'oggetto",
                      'title': "Il titolo della corrispondente voce"
                               "di Wikipedia",
                      'osm_id': "L'identificativo dell'oggetto su"
                                "OpenStreetMap",
                      'osm_type': "Il tipo di oggetto in OpenStreetMap"
                                  "(node, way, relation)"
                      }

        optional = {'dim': "La dimensione lineare dell'oggetto"
                           "ad esempio la sua diagonale nel caso di "
                           "un'edificio",
                    'ref': "La pagina referrer che ti ha inviato qui",
                    'id': "L'id del link che ti ha inviato qui"
                    }
    else:
        parameters = {'lat': lat,
                      'lon': lon,
                      'title': title,
                      'osm_type': osm_types_norm,
                      'osm_id': osm_ids_num
                      }
        optional = {'dim': dim,
                    'ref': referrer,
                    'id': id_
                    }

    return parameters, optional, error


def __get_new_text(old_text, parameters, optional):

    template, new_text, old_text, section = get_new_text(old_text,
                                                         parameters,
                                                         optional
                                                         )

    difftable = get_difftable_difflib(old_text, new_text)

    return new_text, old_text, template, section, difftable


@app.route("/map")
def show_map():
    parameters, optional, error = validate_parameters(request.args)

    if error:
        return render_template('missingparameters.html',
                               parameters=parameters,
                               optional=optional
                               )

    title = parameters['title']

    username = mwoauth_mw.get_current_user(False)

    return render_template('wikimap.html',
                           lat=parameters['lat'],
                           lon=parameters['lon'],
                           osm_id=[str(o) for o in parameters['osm_id']],
                           osm_type=[str(t) for t in parameters['osm_type']],
                           title=title,
                           dim=optional['dim'],
                           referrer=optional['ref'],
                           id=optional['id'],
                           username=username
                           )


@app.route("/anon-edit")
def anon_edit():
    parameters, optional, error = validate_parameters(request.args)

    if error:
        return render_template('missingparameters.html',
                               parameters=parameters,
                               optional=optional
                               )

    title = parameters['title']

    try:
        old_text = wtp.get_wikitext_from_api(title, "it")
    except Exception as e:
        return render_template('error.html', info=e.message)

    new_text, old_text, template, section, difftable = __get_new_text(
        old_text,
        parameters,
        optional)

    return render_template('anon-edit.html',
                           lat=parameters['lat'],
                           lon=parameters['lon'],
                           title=title,
                           dim=optional['dim'],
                           referrer=optional['ref'],
                           id=optional['id'],
                           new_text=new_text,
                           template=template,
                           section=section,
                           difftable=difftable
                           )


def get_domain(url):
    parsed_uri = urlparse(mwoauth_mw.base_url)
    domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
    return domain


@app.route("/preview")
def preview():
    parameters, optional, error = validate_parameters(request.args)

    if error:
        return render_template('missingparameters.html',
                               parameters=parameters,
                               optional=optional
                               )

    next_url = 'preview?'\
               'lat={lat}'\
               '&lon={lon}'\
               '&title={title}'\
               '&dim={dim}'

    next_url = next_url.format(lat=parameters['lat'],
                               lon=parameters['lon'],
                               title=parameters['title'],
                               dim=optional['dim']
                               )

    if optional['ref']:
        next_url = next_url + '&ref={ref}'.format(ref=optional['ref'])

    if optional['id']:
        next_url = next_url + '&id={id}'.format(id=optional['id'])

    if mwoauth_mw.get_current_user(False) is None:
        return redirect('../../app/login?next={next}'.format(next=next_url))
    else:

        title = parameters['title']

        token_req = mwoauth_mw.request({'action': 'query',
                                     'titles': title.replace('_', ' '),
                                     'prop': 'info|revisions',
                                     'rvprop': 'timestamp|user'
                                               '|comment|content',
                                     'rvlimit': 1,
                                     'intoken': 'edit'
                                     })

        try:
            pageid = token_req['query']['pages'].keys()[0]
        except (KeyError, TypeError) as e:
            info = token_req['error']['info']

            if info:
                return render_template('error.html', info=info)
            else:
                return render_template('error.html', info=e.message)

        pages = token_req['query']['pages']

        if pageid == '-1':
            if pages[pageid].get('missing', None) is not None:
                domain = get_domain(mwoauth_mw.base_url)
                return render_template('missing.html',
                                       title=title,
                                       site=domain)

        token = token_req['query']['pages'][pageid]['edittoken']

        revs = token_req['query']['pages'][pageid]['revisions'][0]

        old_text = revs['*']

        new_text, old_text, template, section, difftable = __get_new_text(
            old_text,
            parameters,
            optional)

        return render_template('preview.html',
                               lat=parameters['lat'],
                               lon=parameters['lon'],
                               referrer=optional['ref'],
                               id=optional['id'],
                               difftable=difftable,
                               new_text=new_text,
                               rows=len(new_text.split('\n')),
                               title=title,
                               section=section,
                               template=template,
                               edit_token=token
                               )


def mock_success():
    result = dict()
    result['edit'] = dict()
    result['edit']['result'] = 'Success'
    result['edit']['newrevid'] = 1

    return result


@app.route("/edit", methods=['POST'])
def edit():

    csrf_token = session.pop('_csrf_token', None)
    if not csrf_token or csrf_token != request.form.get('_csrf_token'):
        abort(403)

    if mwoauth_mw.get_current_user(False) is None:
        return 'Something went wrong, you are not logged in'
    else:
        edit_token = request.form['edit_token']
        title = request.form['title']
        new_text = request.form['new_text']
        summary = '[wtosm] aggiunta coordinate'
        section = request.form['section']
        referrer = request.form['referrer']
        id_ = request.form['id']

        edit_query = {'action': 'edit',
                      'title': title,
                      'summary': summary,
                      'text': new_text.encode('utf-8'),
                      'token': edit_token,
                      'format': 'json'
                      }

        if section != '-1':
            edit_query['section'] = section

        result = mwoauth_mw.request(edit_query)
        # result = mock_success()
        # result = mwoauth_mw.mwoauth.post(mwoauth_mw.base_url + '/api.php?',
        #                               data=edit_query
        #                               ).data

        try:
            assert(result['edit']['result'] == 'Success')
            if 'nochange' in result['edit']:
                return render_template('nochange.html',
                                       title=title,
                                       referrer=referrer,
                                       id=id_
                                       )
            elif 'newrevid' in result['edit']:
                return render_template('success.html',
                                       title=title,
                                       summary=summary,
                                       referrer=referrer,
                                       id=id_
                                       )

        except Exception as e:
            try:
                info = result['error']['info']
            except:
                info = None

            if info:
                return render_template('error.html', info=info)
            else:
                return render_template('error.html',
                                       info="Exception: {}".format(e.message))


@app.route("/test/edit", methods=['POST'])
def test_edit():

    csrf_token = session.pop('_csrf_token', None)
    if not csrf_token or csrf_token != request.form.get('_csrf_token'):
        abort(403)

    if mwoauth_mw.get_current_user(False) is None:
        return 'Something went wrong, you are not logged in'
    else:
        edit_token = request.form['edit_token']
        new_text = request.form['new_text']
        summary = '[wtosm] aggiunta coordinate'
        section = request.form['section']

        edit_query = {'action': 'edit',
                      'title': 'Utente:CristianCantoro'
                               '/Sandbox/wtosm',
                      'summary': summary,
                      'text': new_text.encode('utf-8'),
                      'token': edit_token
                      }

        if section != '-1':
            edit_query['section'] = section

        result = mwoauth_mw.request(edit_query)
        # result = mock_success()

        try:
            assert(result['edit']['result'] == 'Success')
            message = 'Well done!'
        except:
            message = 'Oh Noes!'

        return message


@app.route("/test/success")
def test_success():
    return render_template('success.html',
                           title='Wikipedia',
                           summary='Test summary',
                           referrer='/index.html',
                           id=None
                           )


@app.route("/test/nochange")
def test_nochange():
    return render_template('nochange.html',
                           title='Wikipedia',
                           referrer='/index.html',
                           id=None
                           )


if __name__ == "__main__":
    import argparse
    from werkzeug.wsgi import DispatcherMiddleware
    from flask import send_from_directory

    description = 'Flask-based application to edit Wikipedia pages to add '\
                  'coordinates from OSM.'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--host",
                        help="Host over which the application is run. "
                             "[default: localhost]",
                        default="localhost")
    parser.add_argument("--no-debug",
                        help="Disable debug",
                        dest="debug",
                        action="store_false"
                        )
    parser.add_argument("-p", "--port",
                        help="Local port over which the application is run. "
                             "[default: 5000]",
                        type=int,
                        default=5000)

    args = parser.parse_args()

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
    def hello():
        oauth_verifier = request.args.get('oauth_verifier')
        oauth_token = request.args.get('oauth_token')
        if oauth_verifier and oauth_token:
            return redirect('/app/oauth-callback'
                            '?oauth_verifier={oauth_verifier}'
                            '&oauth_token={oauth_token}'.format(
                                oauth_verifier=oauth_verifier,
                                oauth_token=oauth_token)
                            )
        else:
            return redirect('/en_US/index.html')

    @redirect_app.route('/<locale>/<path:path>')
    def base_html(locale, path):
        return send_from_directory(os.path.join('..', 'html', locale), path)

    @redirect_app.route('/app')
    def app_index():
        oauth_verifier = request.args.get('oauth_verifier')
        oauth_token = request.args.get('oauth_token')
        if oauth_verifier and oauth_token:
            return redirect('/app/oauth-callback'
                            '?oauth_verifier={oauth_verifier}'
                            '&oauth_token={oauth_token}'.format(
                                oauth_verifier=oauth_verifier,
                                oauth_token=oauth_token)
                            )
        else:
            return redirect('/app/')

    base_app = Flask(__name__)

    if args.debug:
        base_app.config.update(
            DEBUG=True,
            PROPAGATE_EXCEPTIONS=True
        )

    base_app.wsgi_app = DispatcherMiddleware(redirect_app, {
        '/app': app
    })

    base_app.run(host=args.host,
                 port=args.port,
                 debug=args.debug,
                 )
