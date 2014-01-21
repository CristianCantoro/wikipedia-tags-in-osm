#!/usr/env/python
import os
import sys

# activate virtualenv
# change the path here below with the path to your virtualenv
activate_this = os.path.expanduser("/home/user/.virtualenvs/wtosm/bin/activate_this.py")
execfile(activate_this, dict(__file__=activate_this))

# Change working directory so relative paths (and template lookup) work again
basedir = os.path.dirname('/your/path/to/wikipedia-tags-in-osm/wikipedia-tags-in-osm/app/')
sys.path.append(basedir)
os.chdir(basedir)

from wiki import app as application
# from demo import app as application
application.secret_key = "a-long-secret-app-key"
