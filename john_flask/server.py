
import json
import requests

from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash, jsonify

app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_envvar('settings.py', silent=True)

@app.route('/leaflet_js')
def leaflet_js():
    d = open('/var/www/flask_mapbox/SanbornLots.json','r')
    lots = d.read()
    d.close()
    d = open('/var/www/flask_mapbox/SanbornBlocks.json','r')
    blocks = d.read()
    d.close()
    return render_template('leaflet_js.html',
        blocks=blocks,
        lots=lots
    )
