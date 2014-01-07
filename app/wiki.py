import os
import ConfigParser as configparser
from flask import Flask
from flask_mwoauth import MWOAuth

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


@app.route("/")
def index():
    username = repr(mwoauth.get_current_user(False))
    return "logged in as: " + username + "<br />" + \
           "pippo 5<br />" + \
           '<a href="login">login</a> / <a href="logout">logout</a>'


@app.route("/map")
def show_map():

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
