import os

import pandas as pd
import numpy as np

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from config import postgres_pswd

from flask import Flask, jsonify, render_template, request, Response
from flask_sqlalchemy import SQLAlchemy
import re
from geocoder import Geocoder


#################################################
# Flask Setup
#################################################
app = Flask(__name__)


#################################################
# Database Setup
#################################################
engine = create_engine(
    # f"postgresql://postgres:{postgres_pswd}@18.222.106.38:5432/Reservation"
    f"postgresql+psycopg2://postgres:{postgres_pswd}@18.222.106.38/Reservation"
)

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(engine, reflect=True)

# Save references to each table
address_data = Base.classes.Address_Data
census_data = Base.classes.Census_Data

# Create the locations dataframe with all data, including both statuses
loc_df = pd.read_sql_table("Address_Data", con=engine)
# Create a locations dataframe with reference/seeded/locked locations
ref_loc_df = loc_df[loc_df.Status == "S"]
ref_loc_df = ref_loc_df.loc[:, ["Latitude", "Longitude", "StreetAddress"]]
# Call the geocoder class
geo = Geocoder(ref_loc_df)

#################################################
# lat/long calculation for a data frame
#################################################


def lat_long_calc(loc_df, calc_loc_df):
    """Receives two DataFrames --original info and the one requiring calculation, returns a dictionary with all rows w/lat.long"""

    calc_loc_df["lat_lon"] = calc_loc_df[[
        "StreetAddress"]].applymap(geo.find_closest)
    # Update columns lat/long with the calculated values
    calc_loc_df["Latitude"] = calc_loc_df["lat_lon"].apply(lambda x: x[0])
    calc_loc_df["Longitude"] = calc_loc_df["lat_lon"].apply(lambda x: x[1])
    # Drop the additional column
    calc_loc_df = calc_loc_df.drop(columns=["lat_lon"])
    # Include indices for "merge"
    loc_df = loc_df.reset_index()
    calc_loc_df = calc_loc_df.reset_index()
    loc_df = pd.concat([loc_df, calc_loc_df], sort=False).drop_duplicates(
        ["index"], keep="last"
    )
    # clean the final df
    loc_df = loc_df.drop(columns=["index"]).reset_index(drop=True)

    # Convert the dataframe into a dictionary and return it
    return loc_df.to_dict(orient="records")


#################################################
# Flask Routes
#################################################

# Route to render index.html template using data from db
@app.route("/")
def index():
    """Returns all street names to populate street name dropdown in HTML for selection"""

    # select only StreetAddress and get rid of the number and return only unique values
    select_st = 'select distinct right("StreetAddress", (length("StreetAddress") - position(\' \' in "StreetAddress"))) "StreetAddress"\
        from "Address_Data" a order by "StreetAddress"'
    street_df = pd.read_sql_query(select_st, con=engine)

    # Convert the dataframe into a dictionary
    street_dropdown = street_df.to_dict(orient="records")

    '''Return the homepage'''
    return render_template("indexm.html", street_dropdown=street_dropdown)


@app.route("/api/locations")
def locations():
    """Return all location data to be used in interactive leaflet map"""

    # Create the locations dataframe with all data (all statuses -- S, C, L -- are included)
    loc_df = pd.read_sql_table("Address_Data", con=engine)

    # Create a locations dataframe with only status of c(calculated) aka those without lat/long
    calc_loc_df = loc_df[loc_df.Status == "C"]

    # Calculate lat/long using reference data
    final_df = lat_long_calc(loc_df, calc_loc_df)

    # Return a JSON list of all locations including those with both statuses
    return jsonify(final_df)


@app.route("/filter/<street>", methods=["GET", "POST"])
def filter_street(street):
    """Return all locations for a given street."""

    if request.method == "POST":
        street = request.form["street"]

    # Create the locations dataframe with all data
    loc_df = pd.read_sql_table("Address_Data", con=engine)

    # Filter locations, only those on the required street
    bool_idx = loc_df["StreetAddress"].str.contains(
        street, flags=re.IGNORECASE, regex=True)
    ref_loc_df = loc_df[bool_idx]

    # Determine which ones require lat/long calculation
    calc_loc_df = ref_loc_df[ref_loc_df.Status == "C"]

    # Calculate lat/long using reference data
    final_df = lat_long_calc(ref_loc_df, calc_loc_df)

    print(f"End: {final_df}")
    return jsonify(final_df)


@app.route("/savelocation", methods=["GET", "POST"])
def send_to_db():
    if request.method == "POST":
        request.get_json(force=True)
        loc_chg = request.json['savedCoords']

        # need to fix how data is sent Lat/long are reversed
        for i in range(len(loc_chg)):
            updt_st = f'update "Address_Data" set "Latitude" = {loc_chg[i]["Longitude"]}, "Longitude" = {loc_chg[i]["Latitude"]}, \
                "Status" = \'L\' where "AddressId" = {loc_chg[i]["AddressId"]}'
            engine.execute(updt_st)

        return Response("sent "+str(request.json['savedCoords']), mimetype="application/json")

# return render_template("form.html")


# @app.route("/api/census_data")
# def census_data():

#     census_data = db.session.query(census_data).statement
#     cen_df = pd.read_sql_query(census_data, db.session.bind)
#     combined_df = loc_df.set_index("addressid").join(cen_df.set_index("addressid"))

#     return jsonify(combined_df)


# def filter(filter_array):
#     """Return the data for the selected filters."""
#     filters = ""
#     for i in len(filter_array):
#        filters = filters" and " + filter_array[i].column + "= " + filter_array[i].value
#     selection =
#         combined_df.addressid,
#         combined_df.streetAddress,
#         combined_df.latitude,
#         combined_df.longitude,
#         combined_df.status,
#         combined_df.year,
#         combined_df.lastname,
#         combined_df.givenname,
#         combined_df.relation,
#         combined_df.race,
#         combined_df.gender,
#         combined_df.age,
#         combined_df.occupation,
#         combined_df.ownrent,
#         combined_df.propstat,
#         combined_df.housetype,
#         combined_df.notes,
#         combined_df.srcilename,
#         combined_df.lineitem,


#     census_data = pd.read_sql_query(select_st, con=engine)
#     return(census_data.jsonify())
# #    for i in len(filter_array):
# #        filter_st = filter_st" and " + filter_array[i].column + "= " + filter_array[i].value
# # # Retrieve data from DB
# # select_st = 'select c."Year",c."LastName", c."GivenName", c."Relation", c."Race", c."Gender", \
# #                    c."Occupation", a."StreetAddress", a."Latitude", a."Longitude", a."AddressId" \
# #               from "Census_Data" c, "Address_Data" a \
# #            where c."AddressId" = a."AddressId"' + filter_st
# #


#     results = db.session.query(*sel).filter(combined_df.addressid == addressid).all()


if __name__ == "__main__":
    app.run()

    # DO SOMETHING
