
import json
import requests

from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash, jsonify

app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_envvar('settings.py', silent=True)

MAPBOX_ACCESS_KEY = 'pk.eyJ1IjoiamNtMTAiLCJhIjoiY2sxeHp4anpwMGhpazNkbWxiaXlvdG0xeCJ9.VyvWYqjPKfNOPe2LC96tZQ'



# Mapbox driving direction API call
ROUTE_URL = "https://api.mapbox.com/directions/v5/mapbox/driving/{0}.json?access_token={1}&overview=full&geometries=geojson"

def create_route_url():
    # Create a string with all the geo coordinates
    lat_longs = ";".join(["{0},{1}".format(point["long"], point["lat"]) for point in ROUTE])
    # Create a url with the geo coordinates and access token
    url = ROUTE_URL.format(lat_longs, MAPBOX_ACCESS_KEY)
    return url

def create_stop_location_detail(title, latitude, longitude, index, route_index):
    point = Point([longitude, latitude])
    properties = {
        "title": title,
        'icon': "campsite",
        'marker-color': '#3bb2d0',
        'marker-symbol': index,
        'route_index': route_index
    }
    feature = Feature(geometry = point, properties = properties)
    return feature

def create_stop_locations_details():
    stop_locations = []
    for route_index, location in enumerate(ROUTE):
        if not location["is_stop_location"]:
            continue
        stop_location = create_stop_location_detail(
            location['name'],
            location['lat'],
            location['long'],
            len(stop_locations) + 1,
            route_index
        )
        stop_locations.append(stop_location)
    return stop_locations








def get_route_data():
    # Get the route url
    route_url = create_route_url()
    # Perform a GET request to the route API
    result = requests.get(route_url)
    # Convert the return value to JSON
    data = result.json()

    geometry = data["routes"][0]["geometry"]
    route_data = Feature(geometry = geometry, properties = {})
    waypoints = data["waypoints"]
    return route_data, waypoints


def index():
    return render_template('index.html')


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
@app.route('/mapbox_js')
def mapbox_js():
    d = open('/var/www/flask_mapbox/SanbornLots.json','r')
    lots = d.read()
    d.close()
    d = open('/var/www/flask_mapbox/SanbornBlocks.json','r')
    blocks = d.read()
    d.close()
    return render_template('mapbox_js.html', 
        ACCESS_KEY=MAPBOX_ACCESS_KEY,
        blocks=blocks,
	lots=lots
    )

@app.route('/mapbox_gl')
def mapbox_gl():
    route_data, waypoints = get_route_data()

    stop_locations = create_stop_locations_details()

    # For each stop location, add the waypoint index 
    # that we got from the route data
    for stop_location in stop_locations:
        waypoint_index = stop_location.properties["route_index"]
        waypoint = waypoints[waypoint_index]
        stop_location.properties["location_index"] = route_data['geometry']['coordinates'].index(waypoint["location"])

    return render_template('mapbox_gl.html', 
        ACCESS_KEY=MAPBOX_ACCESS_KEY,
        route_data = route_data,
        stop_locations = stop_locations
    )
