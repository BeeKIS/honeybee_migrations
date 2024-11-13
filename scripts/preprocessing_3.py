#!/usr/bin/env python3

"""
Quick and dirty analysis of colony migrations, continuation from migration_preprocessing_2.

3rd step

script loads excel table to df and queries distance between origin and destination.
Distance is then written in the table in kilometers.

OpenStreetMap + grasshopper is used in queries.
"""
__author__ = "janez presern, anja pavlin, andraz marinc"


import yaml
import matplotlib.pyplot as plt
import pandas as pd
import requests
import numpy as np


def distance_by_roadclass(data):
    """ Parse graphhopper response and calculate distances traveled on each 
    roadtype.
    
    :param data: text.json() parsed graphhopper response (via GET api)
    
    """
    # Get road class.
    details = data['paths'][0]['details']
    road_class_segments = details['road_class']

    for road_segment in details['distance']:
        road_segment.append('default_road_class')
        segment_start, segment_stop = road_segment[0], road_segment[1]

        for class_segment in road_class_segments:
            class_segment_points = range(class_segment[0], class_segment[1])

            if (segment_start in class_segment_points and segment_stop - 1 in class_segment_points):
                road_segment[3] = class_segment[2]

    road_class_distances = dict.fromkeys([i[2] for i in details['road_class']], 0)
    for road_segment in details['distance']:
        road_class_distances[road_segment[3]] += road_segment[2]
    if not road_class_distances.get('motorway'):  # Ensure value at motorway.
        road_class_distances['motorway'] = 0

    return pd.DataFrame.from_dict([road_class_distances])


def get_the_distance(df, url=None):
    dist = []
    dist2 = pd.DataFrame()
    dist_points = pd.DataFrame(columns=["travel_points"])
    dist_failed = pd.DataFrame()
    for i, row in df.iterrows():
        print("Move number: ", str(i))
        
        # Coordinates packaged for use with get api.
        origin = str(row.origin_lat)+','+str(row.origin_long)
        dest = str(row.dest_lat)+','+str(row.dest_long)

        parameters_get = {
                        "profile": "truck2",  # TODO. change this to beekeeper truck.
                        "point": [origin, dest],
                        "elevation": "true",
                        "details": ["road_class", "distance"],
                        "optimize": "true",
                        "distance_influence": 0,
                        "points_encoded": "false", # if false, you get [lon, lat, elevation] form
                        "debug": "false",
                        "calc_points": "true",
                        "ch.disable": "false",
                        "pass_through": "false"}


        # Query graphhopper & parse.
        text = requests.get(url, params=parameters_get)

        if text.json().__contains__('paths'):

            dist.append(np.round(text.json()['paths'][0]['distance'] / 1000, 3))
            dist2 = pd.concat([dist2, distance_by_roadclass(text.json())/1000], ignore_index=True)

            dist2.at[i, "travel_distances"] = np.round(text.json()['paths'][0]['distance'] / 1000, 3)
            dist2.at[i, "travel_time"] = np.round(text.json()['paths'][0]['time'] / 1000, 0) / 60  # from miliseconds to seconds to minutes
            dist_points.at[i, "travel_points"] = text.json()['paths'][0]['points']['coordinates'][::40] # accepting every 40th travel point

        else:
            print('Location data in row are invalid.')
            dist.append(np.nan)
            dist_failed = pd.concat([dist_failed, row.to_frame()], ignore_index=True, axis=1)
            dist2.at[i, "travel_distances"] = np.nan
            dist2.at[i, "travel_time"] = np.nan
            dist2.at[i, "motorway"] = np.nan
            dist_points.at[i, "travel_points"] = []
    return dist, dist_failed.T, pd.concat([dist2, dist_points], axis=1)



if __name__ == "__main__":

    with open("config.yaml") as f:
        CONFIG = yaml.load(f, Loader=yaml.FullLoader)
  
    origins = CONFIG['migrations_processed']
    
    df_migrations = pd.read_excel(origins, sheet_name='CBZ back migrations appended_5')
    df_migrations_0 = pd.read_excel(origins, sheet_name='CBZ back migrations appended_0')

    # Append kilometers to 5 km.
    distances, distances_failed, distance_2 = get_the_distance(df_migrations, CONFIG['hopper_url'])
    df_migrations = pd.concat([df_migrations, distance_2], axis=1)


    # Append kilometers to 0 km.
    distances_0, distances_failed_0, distance_2_0 = get_the_distance(df_migrations_0, CONFIG['hopper_url'])
    df_migrations_0 = pd.concat([df_migrations_0, distance_2_0], axis=1)

    writer = pd.ExcelWriter(origins, engine='openpyxl', mode='a', if_sheet_exists='replace')
    df_migrations.to_excel(writer, sheet_name="migrations distances_5 cutoff", index=False)
    df_migrations_0.to_excel(writer, sheet_name="migrations distances_0 cutoff", index=False)
    distances_failed.to_excel(writer, sheet_name='Failed_5', index=False)
    writer.close()


