#!/usr/bin/env python
# coding: utf-8


# Analysis of colony migrations in Slovenia
# 
# author: Janez Prešern, KIS

 
import yaml
import itertools as it
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import seaborn as sns
import seaborn.objects as so
from shapely import Polygon, LineString, Point
from matplotlib.collections import LineCollection

with open("config.yaml") as f:
    CONFIG = yaml.load(f, Loader=yaml.FullLoader)
    
###########
# Load data
###########

# Load pruned and augmented migrations
migrations_fn = CONFIG['migrations_processed']
df_migrations = pd.read_excel(migrations_fn, sheet_name='CBZ back migrations appended_0')
df_migrations = df_migrations.loc[df_migrations.year != 2023]

# Load pruned and augmented migrations, distances travelled and fuel / toll 
# costs with 5 km cutoff
migrations_augmented_fn = CONFIG['migrations_processed']
df_migrations_augmented = pd.read_excel(migrations_augmented_fn, sheet_name='fuel prices included 5km')
df_migrations_augmented = df_migrations_augmented.loc[df_migrations_augmented.year != 2023]

# Remove the single-direction migrations
mask = df_migrations_augmented.uuid_migration.value_counts()
df_migrations_augmented = df_migrations_augmented.loc[df_migrations_augmented.uuid_migration.isin(mask.index[mask > 1])]


#################################################
# Draw the number of all migrations for each year
#################################################
df_movements_yearly = df_migrations.groupby(df_migrations.year)["uuid"].count().reset_index(name="n_of_migrations")
df_movements_augmented_yearly = df_migrations_augmented.groupby(df_migrations_augmented.year)["uuid"].count().reset_index(name="n_of_migrations")
df_movements_augmented_yearly_small = df_migrations_augmented.loc[df_migrations_augmented.FAMILY_MOVE < 29].groupby(df_migrations_augmented.year)["uuid"].count().reset_index(name="n_of_migrations")

df_movements_augmented_yearly_type = df_migrations_augmented.groupby(["year", "TYPE"])["uuid"].count().reset_index(name="n_of_migrations")
df_colony_movements_yearly = df_migrations.groupby(["year"])["FAMILY_MOVE"].sum().reset_index(name="n_of_colony_migrations")
df_colony_movements_augmented_yearly = df_migrations_augmented.groupby(["year"])["FAMILY_MOVE"].sum().reset_index(name="n_of_colony_migrations")

sns.set_style('white')

f0 = plt.figure(figsize=(8, 8), dpi=200); a00 = f0.add_axes([0.15, 0.55, 0.70, 0.4]); a00_twin = a00.twinx()
sns.barplot(df_movements_yearly, x="year", y="n_of_migrations", ax=a00, color = "darkgrey")
sns.barplot(df_movements_augmented_yearly, x="year", y="n_of_migrations", ax=a00_twin, color="teal")

a00.set_ylabel("Number of migrations per year", fontsize=15, color="grey")
a00.set_xlabel("")
a00.tick_params(axis='y', labelcolor="darkgrey", labelsize=15)
a00_twin.set_ylim(a00.get_ylim())
a00_twin.set_ylabel("Number of migrations\nmore than 8 colonies and more than 5 km", color="teal")
a00_twin.tick_params(axis='y', labelcolor="teal", labelsize=15)
a00.tick_params(axis='both', which='major', labelsize=15)
a00_twin.tick_params(axis='both', which='major', labelsize=15)

a01 = f0.add_axes([0.15, 0.08, 0.70, 0.4]); a01_twin = a01.twinx()
sns.barplot(df_colony_movements_yearly, x="year", y="n_of_colony_migrations", ax=a01, color="darkgrey")
sns.barplot(df_colony_movements_augmented_yearly, x="year", y="n_of_colony_migrations", ax=a01_twin, color="teal")

a01.set_ylabel("Number of migrated colonies", fontsize=15, color="grey")
a01.set_xlabel("Year", fontsize=15)
a01.tick_params(axis='y', labelcolor="darkgrey")
a01_twin.set_ylim(a01.get_ylim())
a01_twin.set_ylabel("Number of migrated colonies\nmore than 8 colonies and more than 5 km", color="teal")
a01_twin.tick_params(axis='y', labelcolor="teal", labelsize=15)

a01.tick_params(axis='both', which='major', labelsize=15)
a01_twin.tick_params(axis='both', which='major', labelsize=15)

sns.set_style('white')

f0.savefig(f'{CONFIG["colony_moves_by_year"]}')

# Construct df for storing stats.
all_stats_migrations_yearly = df_movements_yearly
all_stats_migrations_yearly_augmented = df_movements_augmented_yearly
all_stats_migrations_yearly_augmented_small = df_movements_augmented_yearly_small

all_stats_migrations_colony_yearly = df_colony_movements_yearly
all_stats_migrations_colony_yearly_augmented = df_colony_movements_augmented_yearly


""" load data """


# Number of beekeepers who relocate their colonies.
# Get the number of beekeepers registered in particular year.
origins = CONFIG['origins']
df_origin = pd.read_excel(origins)
df_origin = pd.concat([df_origin.iloc[:, 0:5], df_origin.loc[:, df_origin.columns.str.contains("_10")]], axis=1)
df_origin = df_origin.rename(
    columns={
        "CENSUS_2011_10": 2011, "CENSUS_2012_10": 2012,
        "CENSUS_2013_10": 2013, "CENSUS_2014_10": 2014,
        "CENSUS_2015_10": 2015, "CENSUS_2016_10": 2016,
        "CENSUS_2017_10": 2017, "CENSUS_2018_10": 2018,
        "CENSUS_2019_10": 2019, "CENSUS_2020_10": 2020, 
        "CENSUS_2021_10": 2021, "CENSUS_2022_10": 2022,
        "CENSUS_2023_10": 2023
    }
)

dfdf = df_origin.melt(
    id_vars=[
        "KMG_MID",
        "GMID",

    ], 
    value_vars=[
        2011, 2012, 2013,
        2014, 2015, 2016,
        2017, 2018, 2019,
        2020, 2021, 2022
    ], 
    var_name="year", 
    value_name="census"
)

dfdf = dfdf.dropna(subset="census")   # Remove locations without data on census.
dfdf = dfdf.dropna(subset="KMG_MID")  # Remove locations without unique ID.
dfdf = dfdf.loc[dfdf.census > 0]      # Remove locations with 0 colonies.

df_origin_stats = dfdf.groupby("year")["KMG_MID"].nunique().to_frame()

# Get migrations
KMG_MID_migrated = df_migrations.groupby('year')["KMG_MID_origin"].nunique().to_frame(name="n_of_migrations")
KMG_MID_migrated_augmented = df_migrations_augmented.groupby('year')["KMG_MID_origin"].nunique().to_frame(name="n_of_migrations")
KMG_MID_migrated_augmented_small = df_migrations_augmented.loc[df_migrations_augmented.FAMILY_MOVE < 29].groupby('year')["KMG_MID_origin"].nunique().to_frame(name="n_of_migrations")


#################################
# Draw colony migrations per week
#################################
# First, we draw for all years, then we do it year by year.
df_dest0 = df_migrations_augmented.groupby(by=["week"])["FAMILY_MOVE"].sum().to_frame(name="n_of_migrations")
f1 = plt.figure(figsize=(8, 4), dpi=200); a10 = f1.add_axes([0.15, 0.15, 0.8, 0.75])
sns.lineplot(df_dest0, x="week", y="n_of_migrations", markers="o")
a10.set_title("Število premaknjenih družin po tednih - vsota 2014 - 2022")

all_stats_weekly_migrations = df_dest0


df_dest = df_migrations.groupby(by=["year", "week"])["FAMILY_MOVE"].sum()
df_dest = df_dest.to_frame().reset_index()

all_stats_weekly_migration_yearly = df_dest

df_dest_augmented = df_migrations_augmented.groupby(by=["year", "week"])["FAMILY_MOVE"].sum()
df_dest_augmented = df_dest_augmented.to_frame().reset_index()
grid2 = sns.FacetGrid(df_dest_augmented, col="year", hue="year", palette="tab20c",
                 col_wrap=3, height=1.5, despine=False)
grid2.fig.subplots_adjust(wspace=0, hspace=0)
grid2.fig.set_size_inches(15.5, 15.5)
grid2.map(plt.plot, "week", "FAMILY_MOVE", marker="o")
grid2.set_ylabels("Colonies migrated", size=14)
grid2.set_xlabels("Week", size=15)
grid2.set_titles(size=15)
grid2.tick_params(axis='both', which='major',labelsize=15)

grid2.fig.savefig(f'{CONFIG["yearly_migration_dynamics"]}')

all_stats_weekly_migration_yearly = df_dest
all_stats_weekly_migration_yearly_augmented = df_dest_augmented


# Get number of colonies in a single migration.
# How are the colonies packed for a single migration? This should reveal sizes 
# of typical container units and their frequency.
df_n_of_colonies_in_package = pd.cut(
    df_migrations["FAMILY_MOVE"], 
    bins=np.arange(0, 221, 1)
).value_counts().to_frame(name="Število družin v premiku").reset_index()


df_n_of_colonies_in_package_augmented = pd.cut(
    df_migrations_augmented["FAMILY_MOVE"],
    bins=np.arange(0, 221, 1)
).value_counts().to_frame(name="Number of colonies migrated").reset_index()

f2_1 = plt.figure(figsize=(8, 4), dpi=200); a20_1 = f2_1.add_axes([0.15, 0.15, 0.8, 0.75])


sns.histplot(data=df_migrations_augmented["FAMILY_MOVE"], bins=np.arange(0, 221, 1), ax=a20_1, color="teal")

a20_1.set_ylabel("No. of migrations", fontsize=15)
a20_1.set_xlabel("No. of colonies packed in single migration", fontsize=15)
a20_1.set_title("Colony packaging by migration", fontsize=15)
a20_1.set_xlim(0, 100)

a20_1.tick_params(axis='both', labelsize=15)
sns.set_style('white')

f2_1.savefig(f'{CONFIG["colony_packaging"]}')

# Load data about migrations survey.
survey_fn = CONFIG['survey_results']
df_survey = pd.read_excel(survey_fn, sheet_name='transport_means')


all_stats_colony_packaging = df_n_of_colonies_in_package
all_stats_colony_packaging_pruned = df_n_of_colonies_in_package_augmented


df_movements_yearly = df_migrations_augmented.groupby(
    df_migrations_augmented.year
)["travel_distances"].sum().reset_index(name="razdalja [km]")

df_movements_yearly_small = df_migrations_augmented.loc[
    df_migrations_augmented.FAMILY_MOVE < 29
].groupby(df_migrations_augmented.year)["travel_distances"].sum().reset_index(name="razdalja [km]")

df_movements_per_beekeeper = df_migrations_augmented["travel_distances"].describe().reset_index()

sns.set_style("white")
f6 = plt.figure(figsize=(8, 4), dpi=200); a60 = f6.add_axes([0.15, 0.15, 0.68, 0.75]); a60_twin = a60.twinx()

sns.barplot(df_movements_yearly, x="year", y="razdalja [km]", color="teal", ax=a60)
sns.barplot(df_movements_yearly_small, x="year", y="razdalja [km]", color="black", ax=a60_twin)

a60.set_ylabel("Cumulative travel distance [km]", fontsize=15, color="teal")
a60_twin.set_ylabel("Cumulative travel distance\n by small beekeepers [km]", fontsize=15)
a60.set_xlabel("Year", fontsize=15)

a60.tick_params(axis='both', which='major', labelsize=15)
a60.tick_params(axis='y', color="teal", labelcolor="teal")
a60_twin.tick_params(axis='both', which='major', labelsize=15)
a60_twin.set_ylim(a60.get_ylim())

sns.set_style('white')

f6.savefig(f'{CONFIG["yearly_distances_traveled_cumulative"]}')

all_stats_migration_distances_yearly = df_movements_yearly
all_stats_migration_distances_yearly_small = df_movements_yearly_small
all_stats_migrations_distances_per_beekeper = df_movements_per_beekeeper

############################################
# Obtain general beekeeping and apiary stats
############################################


# Calculate fuel consumption and toll expenditures in a given year.
df_fuel = df_migrations_augmented.groupby('year')["fuel paid"].sum().reset_index()
df_migrations_augmented["toll Euro 0 - 2"] = df_migrations_augmented["motorway"]*df_migrations_augmented["Euro 0 - 2"]
df_toll_euro0_2 = df_migrations_augmented.groupby('year')["toll Euro 0 - 2"].sum().reset_index()
df_migrations_augmented["toll Euro 6, EEV"] = df_migrations_augmented["motorway"]*df_migrations_augmented["Euro 6, EEV"]
df_toll_euro6 = df_migrations_augmented.groupby('year')["toll Euro 6, EEV"].sum().reset_index()
df_cost_euro0 = df_fuel["fuel paid"] + df_toll_euro0_2["toll Euro 0 - 2"]
df_cost_euro6 = df_fuel["fuel paid"] + df_toll_euro6["toll Euro 6, EEV"]
df_cost_total = pd.DataFrame(
    {
        "year": df_fuel["year"],
        "fuel costs only": df_fuel["fuel paid"],
        "total cost Euro 0 - 2": df_cost_euro0, 
        "total cost Euro 6, EEV": df_cost_euro6
    }
)

# Plot yearly costs of fuel and toll.
f_fuel = plt.figure(figsize=(8, 4), dpi=200)
a_fuel = f_fuel.add_axes((0.15, 0.15, 0.80, 0.75))
sns.set_style('white')
sns.barplot(data=df_cost_total, x="year", y="total cost Euro 0 - 2", color="darkgrey", ax=a_fuel, label="toll Euro 0 - 2")
sns.barplot(data=df_cost_total, x="year", y="total cost Euro 6, EEV", color="lightgrey", ax=a_fuel, label="toll Euro 6, EEV")
sns.barplot(data=df_fuel, x="year", y="fuel paid", ax=a_fuel, color="teal", label="fuel")
a_fuel.set_ylabel('Yearly costs of hive transport in €', fontsize=15)
a_fuel.set_xlabel('Year', fontsize=15)
a_fuel.tick_params(axis='both', which='major', labelsize=15)
a_fuel.legend()
sns.set_style('white')
f_fuel.savefig(f'{CONFIG["yearly_costs_fig"]}')

# Plot travel times.
df_traveled_distances = pd.cut(df_migrations_augmented["travel_distances"], bins=np.arange(0, 300, 5)).value_counts().to_frame(name="Kilometers traveled").reset_index()
df_traveled_motorway = pd.cut(df_migrations_augmented["motorway"], bins=np.arange(0, 300, 5)).value_counts().to_frame(name="Kilometers on motorway").reset_index() 
df_traveled_distances = pd.cut(df_migrations_augmented["travel_time"], bins=np.arange(0, 300, 5)).value_counts().to_frame(name="Kilometers traveled").reset_index()
f_traveled_distances = plt.figure(figsize=(8, 4.2), dpi=200)
a_traveled_distances = f_traveled_distances.add_axes((0.15, 0.15, 0.80, 0.75))
sns.set_style('white')
sns.histplot(data=df_migrations_augmented["travel_time"], bins=np.arange(0, 300, 5), ax=a_traveled_distances, color="teal")
a_traveled_distances.set_xlabel("Travel times within single migration [minutes]", fontsize=15)
a_traveled_distances.set_ylabel("Count", fontsize=15)
a_traveled_distances.tick_params(axis='both', labelsize=15)
f_traveled_distances.savefig(f'{CONFIG["travel_time_fig"]}')

############
# Save stats
############

writer = pd.ExcelWriter(CONFIG['migration_stats'])

# General data on beekeepers.
df_origin_stats.to_excel(writer, sheet_name="Number of beekeepers per year")
KMG_MID_migrated.to_excel(writer, sheet_name='Beekeepers that migrated')
KMG_MID_migrated_augmented.to_excel(writer, sheet_name='Beekeepers that migrated pruned')
KMG_MID_migrated_augmented_small.to_excel(writer, sheet_name='Small beekprs migrated pruned')

# General data on migrations.
all_stats_migrations_yearly.to_excel(writer, sheet_name='Migrations yearly')
all_stats_migrations_yearly_augmented.to_excel(writer, sheet_name='Migrations yearly pruned')
all_stats_migrations_yearly_augmented_small.to_excel(writer, sheet_name='Migrations yearly pruned-small')

all_stats_migrations_colony_yearly.to_excel(writer, sheet_name="Colony migrations yrly")
all_stats_migrations_colony_yearly_augmented.to_excel(writer, sheet_name='Colonies migrated pruned')

# General data on weekly migrations yearly.
all_stats_weekly_migration_yearly.to_excel(writer, sheet_name='Weekly migrations, yearly')
all_stats_weekly_migration_yearly_augmented.to_excel(writer, sheet_name='Weekly migrations pruned yearly')

# Colony packaging in migrations.
all_stats_colony_packaging.to_excel(writer, sheet_name="Colony packaging")
all_stats_colony_packaging_pruned.to_excel(writer, sheet_name="Colony packaging pruned")

# Distances.
all_stats_migration_distances_yearly.to_excel(writer, sheet_name="Traveled distances")
all_stats_migration_distances_yearly_small.to_excel(writer, sheet_name="Migrations yearly - small")
all_stats_migrations_distances_per_beekeper.to_excel(writer, sheet_name="Travel - descriptive stats")

# Fuel and toll.
df_cost_total.to_excel(writer, sheet_name="Costs of transport, fuel, toll")

writer.close()

