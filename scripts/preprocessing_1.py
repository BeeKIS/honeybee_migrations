#!/usr/bin/env python3
""" 
Analysis of colony migrations, continuation from migration_preprocessing_1:
    0) splits dataset year-by-year
    1) filters away the migrations, shorter than 0, 3, 5 km (air distance)
    2) considers only migrations, starting in CBS/CBP apiaries, drops the rest
    3) grabs single movement, assigns unique voucher and traces it through year, 
        constructing new df
    4) in case if no migration was done from CBZ (temporary apiary), assume one 
        (to GMID of origin).

"""

__author__ = "janez presern, anja pavlin, andraz marinc"


import yaml
import matplotlib.pyplot as plt
import pandas as pd
import uuid
from datetime import timedelta
import numpy as np
import warnings
from preprocessing_2 import get_the_distance
import seaborn as sns





def add_CBZ_back_trip(uuids, t_df):
    """ 
    t_df: temp_df
    uuuids: list of uids on that particular trip
    
    function that generates the back trip
    first check if a single trip is in the question

    returns generated trip and amended uuids list
    """
    uuid_new = uuid.uuid4().__str__()
    back_trip = pd.Series()
    back_trip["uuid"] = uuid_new
    uuids_ammended = uuids + [uuid_new]

    if len(uuids) == 1:

        u = uuids[0]

        back_trip["GMID_origin"] = t_df.loc[t_df["uuid"] == u]["GMID_dest"].values[0]
        back_trip["GMID_dest"] = t_df.loc[t_df["uuid"] == u]["GMID_origin"].values[0]
        back_trip["DATE_MOVE"] = (t_df.loc[t_df["uuid"] == u]["DATE_MOVE"] + timedelta(days=30)).values[0]
        back_trip["FAMILY_MOVE"] = t_df.loc[t_df["uuid"] == u]["FAMILY_MOVE"].values[0]

        """ coordinates """
        back_trip["X_COORDINATE"] = t_df.loc[t_df["uuid"] == u]["X_origin"].values[0]
        back_trip["Y_COORDINATE"] = t_df.loc[t_df["uuid"] == u]["Y_origin"].values[0]
        back_trip["X_origin"] = t_df.loc[t_df["uuid"] == u]["X_COORDINATE"].values[0]
        back_trip["Y_origin"] = t_df.loc[t_df["uuid"] == u]["Y_COORDINATE"].values[0]
        back_trip["dest_long"] = t_df.loc[t_df["uuid"] == u]["origin_long"].values[0]
        back_trip["dest_lat"] = t_df.loc[t_df["uuid"] == u]["origin_lat"].values[0]
        back_trip["origin_long"] = t_df.loc[t_df["uuid"] == u]["dest_long"].values[0]
        back_trip["origin_lat"] = t_df.loc[t_df["uuid"] == u]["dest_lat"].values[0]

        """ date_time """
        back_trip["year"] = back_trip["DATE_MOVE"].year
        back_trip["month"] = back_trip["DATE_MOVE"].month
        back_trip["week"] = back_trip["DATE_MOVE"].isocalendar().week
        back_trip["DayinYear"] = back_trip["DATE_MOVE"].dayofyear

        """ apiary type, KMG_MID """
        back_trip["TYPE"] = "CBS"
        back_trip["TYPE_origin"] = "CBZ"
        back_trip["KMG_MID_dest"] = t_df.loc[t_df["uuid"] == u]["KMG_MID_origin"].values[0]
        back_trip["KMG_MID_origin"] = ""

        "flags"
        back_trip["flag"] = 1
        back_trip["generated_trip_flag"] = 1

        back_trip = back_trip.to_frame().T

        t_new = pd.concat([t_df.loc[t_df.uuid.isin(uuids)], back_trip], ignore_index=True)

    else:
        # In this case we need to re-calculate the paths. 
        #   - the last known CBS/CBP is excluded OR
        #   - the first known CBS/CBP is excluded

        u = t_df.loc[(t_df.uuid.isin(uuids)) & ((t_df["TYPE_origin"] == "CBS") | (t_df["TYPE_origin"] == "CBP"))]["uuid"].head(n=1).to_list()[0]
        u_CBZ = uuids[-1]

        """ set destination: parameters from last move to CBS """
        back_trip["GMID_origin"] = t_df.loc[t_df["uuid"] == u]["GMID_dest"].values[0]
        back_trip["GMID_dest"] = t_df.loc[t_df["uuid"] == u]["GMID_origin"].values[0]
        back_trip["dest_long"] = t_df.loc[t_df["uuid"] == u]["origin_long"].values[0]
        back_trip["dest_lat"] = t_df.loc[t_df["uuid"] == u]["origin_lat"].values[0]

        back_trip["X_COORDINATE"] = t_df.loc[t_df["uuid"] == u]["X_origin"].values[0]
        back_trip["Y_COORDINATE"] = t_df.loc[t_df["uuid"] == u]["Y_origin"].values[0]

        back_trip["TYPE"] = "CBS"
        back_trip["TYPE_origin"] = "CBZ"
        back_trip["KMG_MID_dest"] = t_df.loc[t_df["uuid"] == u]["KMG_MID_origin"].values[0]
        back_trip["KMG_MID_origin"] = ""

        """ set destination: parameters from the last move to CBZ """
        back_trip["DATE_MOVE"] = (t_df.loc[t_df["uuid"] == u_CBZ]["DATE_MOVE"] + timedelta(days=30)).values[0]
        back_trip["FAMILY_MOVE"] = t_df.loc[t_df["uuid"] == u_CBZ]["FAMILY_MOVE"].values[0]
        back_trip["origin_long"] = t_df.loc[t_df["uuid"] == u_CBZ]["dest_long"].values[0]
        back_trip["origin_lat"] = t_df.loc[t_df["uuid"] == u_CBZ]["dest_lat"].values[0]
        back_trip["X_origin"] = t_df.loc[t_df["uuid"] == u_CBZ]["X_COORDINATE"].values[0]
        back_trip["Y_origin"] = t_df.loc[t_df["uuid"] == u_CBZ]["Y_COORDINATE"].values[0]

        """ date_time """
        back_trip["year"] = back_trip["DATE_MOVE"].year
        back_trip["month"] = back_trip["DATE_MOVE"].month
        back_trip["week"] = back_trip["DATE_MOVE"].isocalendar().week
        back_trip["DayinYear"] = back_trip["DATE_MOVE"].dayofyear

        back_trip = back_trip.to_frame().T


        "flags"
        back_trip["flag"] = 1
        back_trip["generated_trip_flag"] = 1

        t_new = pd.concat([t_df.loc[t_df.uuid.isin(uuids)], back_trip], ignore_index=True)

    """ add key to single out migrations belonging together """
    t_new["uuid_migration"] = uuid.uuid4().__str__()

    return uuids_ammended, t_new

    pass


if __name__ == "__main__":
    with open("config.yaml") as f:
        CONFIG = yaml.load(f, Loader=yaml.FullLoader)

    # Load tables.
    migrations_fn = CONFIG['migrations_processed']
    df_migrations = pd.read_excel(migrations_fn, sheet_name='migrations pruned')
    print("Number of movements: ", df_migrations.shape[0])

    """ get years """
    years = df_migrations.year.unique().tolist()

    writer = pd.ExcelWriter(migrations_fn, mode='a', engine='openpyxl', if_sheet_exists='replace')

    """ set air distances """
    air_gap = [0, 3, 5]


    for gap in air_gap:

        """ 
        prepare empty df
        df will have
        1) unique identificator of first move
        2) list of all sequential moves
        3) list of flags whether the move was added (CBZ - automatic return) or not 
        """
        digest_df = pd.DataFrame()

        """ generate unique id for every migration """

        """ loop over years """
        """ write the movements into new df """
        """ create missing migrations (CBZ --- > CBS) """
        uuid_df = pd.DataFrame(columns=[["year", "sequence"]])
        uuid_df["sequence"] = uuid_df["sequence"].astype('object')

        """ construct new data frame"""
        new_df = pd.DataFrame()

        """ counters """
        counter_uuid_df = 0
        counter = 0

        for y in years:

            """ select years and stationary apiaries only """
            temp_df = df_migrations.loc[(df_migrations["year"] == y) & (df_migrations["air_distance"] >= gap)].copy()

            """ drop fewer than 8 colonies if gap = 0"""
            if gap != 0:

                """ trying to remove remove migrations shorter than 8 km and those that are migrated to anotehr KMG-MID. Move to another KMG-MID could be purchase; however, no proofs given """

                """ trying to remove remove migrations shorter than 8 km only """
                temp_df = temp_df.loc[(temp_df["FAMILY_MOVE"] >= 8)]

            stationary_origins = temp_df.loc[(temp_df["TYPE_origin"] == "CBS") | (temp_df["TYPE_origin"] == "CBP")].index

            """ set up flags to verify if migration already used in analysis """
            temp_df["flag"] = 0
            temp_df["generated_trip_flag"] = 0

            """ take a migration and look for possible continuation of migration. Check if migration has been used previously """
            for i in stationary_origins:
                counter_uuid_df += 1
                row = temp_df.loc[i]

                """ check if row already used: if so, skip the migration """
                if (row["flag"] == 1):
                    continue

                else:

                    """ flags """
                    uuid_next = []
                    uuid_old = []
                    uuid_chain = []

                    """ check if there are onward travels from the destination """
                    if temp_df.loc[(temp_df.GMID_origin== row.GMID_dest) & (temp_df.index > i)].shape[0] > 0:
                        print("Chaining: more than one move")
                        uuid_chain.append(row.uuid)
                        print("\tFirst move: ", row.GMID_origin, " ---> ", row.GMID_dest, " uuid: ", row.uuid)
                        uuid_next = temp_df.loc[(temp_df.GMID_origin== row.GMID_dest) & (temp_df.index > i)]["uuid"].values[0]
                        uuid_chain.append (uuid_next)
                        print("\tNext move: ", row.GMID_dest, " ---> ",
                              str(temp_df.loc[(temp_df.GMID_origin== row.GMID_dest) & (temp_df.index > i)]["GMID_dest"].values[0]),
                              " uuid: ", uuid_next)

                        while uuid_next != uuid_old:
                            temp_GMID_dest = temp_df.loc[temp_df.uuid == uuid_next]["GMID_dest"].values[0]
                            i_next = temp_df.loc[temp_df.uuid == uuid_next]["GMID_dest"].index[0]
                            uuid_old = uuid_next

                            if temp_df.loc[(temp_df.GMID_origin== temp_GMID_dest) & (temp_df.index > i_next)]["uuid"].shape[0] > 0:
                                uuid_next = temp_df.loc[(temp_df.GMID_origin== temp_GMID_dest) & (temp_df.index > i_next)]["uuid"].values[0]
                                uuid_chain.append(uuid_next)
                                print("\tNext move: ", temp_GMID_dest, " ---> ",
                                      str(temp_df.loc[(temp_df.GMID_origin== temp_GMID_dest) & (temp_df.index > i_next)]["GMID_dest"].values[0]),
                                      " uuid: ", uuid_next)
                            else:
                                continue

                        """ set row as already used and that records are older than """
                        temp_df.loc[temp_df.uuid.isin(uuid_chain), "flag"] = 1

                    else:
                        print("Only a single move.")
                        print("\tMove: ", row.GMID_origin, " ---> ", row.GMID_dest, " uuid: ", row.uuid)
                        uuid_chain.append(row.uuid)

                        """ set row as already used and that records are older than """
                        temp_df.loc[temp_df.uuid.isin(uuid_chain), "flag"] = 1

                    """ check if chain ends with CBZ """
                    if temp_df.loc[temp_df.uuid == uuid_chain[-1]]["TYPE"].tolist()[0] == "CBZ":
                        print("Move ends with temporary apiary. Number of moves: ", len(uuid_chain))
                        counter = counter + 1

                        uuid_chain, new_migration = add_CBZ_back_trip(uuid_chain, temp_df)
                        pass

                    else:
                        new_migration = temp_df.loc[temp_df.uuid.isin(uuid_chain)]

                        """ add key to single out migrations belonging together """
                        new_migration["uuid_migration"] = uuid.uuid4().__str__()

                    new_df = pd.concat([new_df, new_migration], ignore_index=True)
                    print("\nNew DF shape: ", str(new_df.shape))

        new_df.to_excel(writer, sheet_name='CBZ back migrations appended_' + str(gap))
    """ measure the number of colonies moved to temporary stands """

    writer.close()
