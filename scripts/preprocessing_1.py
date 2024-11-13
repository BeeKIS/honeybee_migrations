#!/usr/bin/env python3
""" Anaylsis of colony migrations. Preprocessing of migration data. 

First preprocessing step:
    1. Open census, migrations
    2. Transform datetimes
    3. Assign coordinates of origin, remove empty coordinates and cut 
    out coordinates clearly erroneous, such as being outside of boundaries of 
    Slovenia.

"""
__author__ = "janez presern, anja pavlin, andraz marinc"

import yaml
import matplotlib.pyplot as plt
import pandas as pd
import geopandas as gpd
import numpy as np
import uuid
import timeit



if __name__ == "__main__":
    with open("config.yaml") as f:
        CONFIG = yaml.load(f, Loader=yaml.FullLoader)

    # Load data.
    origins = CONFIG['origins']
    df_origin = pd.read_excel(origins, sheet_name='Export Worksheet', usecols="A:D")

    destinations = CONFIG['destinations']
    df_destination = pd.read_excel(destinations, sheet_name='Export Worksheet')

    # Assign years, months.
    df_destination["year"] = df_destination.DATE_MOVE.dt.year
    df_destination["month"] = df_destination.DATE_MOVE.dt.month
    df_destination["week"] = df_destination.DATE_MOVE.dt.isocalendar().week
    df_destination["DayinYear"] = df_destination.DATE_MOVE.dt.dayofyear

    """ type of apiary at origin """
    df_destination["TYPE_origin"] = ""
    df_origin["TYPE_origin"] = "CBS"

    #############################
    # Prepare origin coordinates.
    #############################
    """ coordinates of the origin """
    print("Mapping the coordinates of GMID from Origin")


    """ create working copy """
    df_main = pd.DataFrame()

    for i, row in df_destination.iterrows():

        """ make separate independent copy"""
        temp_df = row.copy(deep=True).to_frame().T

        """ find KMG-MIDs in the table of stationary apiaries """
        if df_origin.loc[df_origin["GMID"] == row["GMID_origin"]]["KMG_MID"].any():
            temp_df["KMG_MID_origin"] = df_origin.loc[df_origin["GMID"] == row["GMID_origin"]]["KMG_MID"].iloc[0]

        if df_origin.loc[df_origin["GMID"] == row["GMID_dest"]]["KMG_MID"].any():
            temp_df["KMG_MID_dest"] = df_origin.loc[df_origin["GMID"] == row["GMID_dest"]]["KMG_MID"].iloc[0]

        """ X_origin, Y_origin, TYPE_origin """
        if df_origin.loc[df_origin["GMID"] == row["GMID_origin"]]["X_COORDINATE"].any():
            temp_df["X_origin"] = df_origin.loc[df_origin["GMID"] == row["GMID_origin"]]["X_COORDINATE"].iloc[0]
            temp_df["Y_origin"] = df_origin.loc[df_origin["GMID"] == row["GMID_origin"]]["Y_COORDINATE"].iloc[0]
            temp_df["TYPE_origin"] = df_origin.loc[df_origin["GMID"] == row["GMID_origin"]]["TYPE_origin"].iloc[0]

        if row["GMID_origin"] < 100000:

            temp_df["TYPE_origin"] = "CBZ"

        df_main = pd.concat([df_main, temp_df], ignore_index=True, axis=0)

    ###############
    # QUALITY CHECK
    ###############
    """ remove empty coordinates """
    df_main = df_main.dropna(subset=['X_COORDINATE'])
    df_main = df_main[df_main['X_COORDINATE'] > 0]

    """ how many rows without KMG_MID"""

    df_main = df_main[(df_main['X_COORDINATE'] >= 31118.3) & (df_main['X_COORDINATE'] <= 373217.65)]
    df_main = df_main[(df_main['Y_COORDINATE'] >= 194661.55) & (df_main['Y_COORDINATE'] <= 625999.74)]

    """ generate unique id for every migration """
    df_main['uuid'] = df_main.index.map(lambda _: uuid.uuid4())

    """ 
    create independent working copy 
    adding two more column values
    """
    print("Creating working copy")
    df_main_copy = df_main.copy(deep=True)


    """ Assign origin coordinates for when missing.
    in some cases, it is impossible to infer the trip origin, for example, 
    when trip starts with CBZ. If so, no ORIGIN coordinates can be found in 
    table with stationary apiaries.
    
    We search ORIGIN under DEST to look for missing data. The rationale being 
    every trip (especially to CBZ) must be recorded somewhere; exceptions are 
    only CBZ for newly-created apiaries, which are not supposed to be recorded
    in the migration database.
    
        1. Find migrations without TYPE_origin
        2. Check if X_origin is missing, too.
        3. find the coordinates in DEST column, assignes them to missing ORIGINS
    
    """

    print("Travels starting at temporary apiary, ORIGIN not yet known since it wasn't in the stationary database")
    print(df_main_copy[(df_main_copy["X_origin"].isna()) & (df_main_copy.GMID_origin < 100000)].shape)



    unassigned_UNK_ix = df_main_copy[(df_main_copy["X_origin"].isna())].index
    for ix in unassigned_UNK_ix:
        # Get GMID.
        unassigned_GMID = df_main.loc[ix]["GMID_origin"]
        """ check if there is a record of GMID in the destination column and poaches the coordinates and types """
        if df_main_copy.loc[df_main["GMID_dest"] == unassigned_GMID].shape[0] == 1:
            df_main_copy.loc[ix, "X_origin"] = df_main.loc[df_main["GMID_dest"] == unassigned_GMID].X_COORDINATE.values[0]
            df_main_copy.loc[ix, "Y_origin"] = df_main.loc[df_main["GMID_dest"] == unassigned_GMID].Y_COORDINATE.values[0]
            df_main_copy.loc[ix, "KMG_MID_origin"] = df_main.loc[df_main["GMID_dest"] == unassigned_GMID].KMG_MID_dest.values[0]
            df_main_copy.loc[ix, "TYPE_origin"] = "CBZ"

        elif df_main_copy.loc[df_main["GMID_dest"] == unassigned_GMID].shape[0] > 1:
            df_main_copy.loc[ix, "X_origin"] = df_main.loc[df_main["GMID_dest"] == unassigned_GMID].X_COORDINATE.iloc[0]
            df_main_copy.loc[ix, "Y_origin"] = df_main.loc[df_main["GMID_dest"] == unassigned_GMID].Y_COORDINATE.iloc[0]
            df_main_copy.loc[ix, "KMG_MID_origin"] = df_main.loc[df_main["GMID_dest"] == unassigned_GMID].KMG_MID_dest.iloc[0]
            df_main_copy.loc[ix, "TYPE_origin"] = "CBZ"
        else:
            pass

    print("Still unassigned origin coordinate for travels originated:",
          df_main_copy[(df_main_copy["X_origin"].isna())].shape[0])
    print("No of moves with no origin in file: ", str(df_main_copy.loc[df_main_copy["TYPE_origin"].isna()].shape[0]),
          " These are mostly cross-border moves?")

    """ QUALITY CHECK   """
    """ clip bounds - check if coordinates are within Slovenia """
    """ remove empty coordinates """
    """ repeat coordinate filtering, this time for origin! """
    df_main_copy = df_main_copy[(df_main_copy['X_origin'] >= 31118.3) & (df_main_copy['X_origin'] <= 373217.65)]
    df_main_copy = df_main_copy[(df_main_copy['Y_origin'] >= 194661.55) & (df_main_copy['Y_origin'] <= 625999.74)]
    df_main_copy = df_main_copy.dropna(subset=['X_origin'])
    df_main_copy = df_main_copy[df_main_copy['X_origin'] > 0]

    print(
        'Number of movements after removal of those with missing coordinates '
        'and of those outside of Slovenia: ', 
        df_main_copy.shape[0]
        )

    """ add lat and longitude WGS84 (EPSG 4326) """
    print("Converting to WGS84 CRS")
    df_dest_longlat = gpd.GeoDataFrame(df_main_copy, geometry=gpd.points_from_xy(x=df_main_copy.Y_COORDINATE, y=df_main_copy.X_COORDINATE, crs='EPSG:3794'))
    df_dest_longlat = df_dest_longlat.to_crs('EPSG:4326')
    df_main_copy["dest_long"] = df_dest_longlat.geometry.x
    df_main_copy["dest_lat"] = df_dest_longlat.geometry.y

    df_origin_longlat = gpd.GeoDataFrame(df_main_copy, geometry=gpd.points_from_xy(x=df_main_copy.Y_origin, y=df_main_copy.X_origin, crs='EPSG:3794'))
    df_origin_longlat = df_origin_longlat.to_crs('EPSG:4326')
    df_main_copy["origin_long"] = df_origin_longlat.geometry.x
    df_main_copy["origin_lat"] = df_origin_longlat.geometry.y

    """ drop the useless and sort the columns """
    df_main_copy = df_main_copy.drop(columns="HS_MID")

    """ air distance """
    df_main_copy["X_COORDINATE"] = df_main_copy["X_COORDINATE"].astype('float')
    df_main_copy["Y_COORDINATE"] = df_main_copy["Y_COORDINATE"].astype('float')
    df_main_copy.loc[:, "air_distance"] = np.hypot(np.abs(df_main_copy["X_origin"] - df_main_copy["X_COORDINATE"]),
             np.abs(df_main_copy["Y_origin"] - df_main_copy["Y_COORDINATE"])) / 1000

    writer = pd.ExcelWriter(CONFIG['migrations_processed'], engine='openpyxl')

    df_main_copy.to_excel(writer, sheet_name="migrations pruned", index=False)

    writer.close()

    pass
