"""
backoffice : The main application
"""

import sys
from flask import Flask

sys.path.insert(1, "../../../backo")

from collections_set import countries, people
from backo import Backoffice, current_user, log_system

log_system.add_handler(log_system.set_streamhandler())


# set the flask application route
flask = Flask("nationality")


myapp = Backoffice("nationality")
myapp.add_collection(countries)
myapp.add_collection(people)
myapp.add_routes(flask, "")


# ------------------------------------
# Initialisation
# ------------------------------------
current_user.standalone = True

people.drop()

current_user.standalone = False


if __name__ == "__main__":
    flask.run(host="0.0.0.0", port=5000)
