#!/usr/bin/env python3
""" Models travel costs using the same calibration as in fuel calculation.

"""
import yaml
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from utils import decay_exp2, rise_exp2, linear, r_square, unp_decay_exp2, unp_rise_exp2
from scipy.optimize import curve_fit, minimize
import uncertainties as unc
import uncertainties.unumpy as unp
from RegscorePy import aic
from lmfit import Model
import seaborn as sns

__author__ = "jpresern"


if __name__ == "__main__":
    with open('config.yaml') as f:
        CONFIG = yaml.load(f, Loader=yaml.FullLoader)
    
    # Fuel consumption calibration params.
    fuel_calib = CONFIG["fuel_calibrations"]
    df_consumption = pd.read_excel(fuel_calib, sheet_name='fuel_calibration')

    # Honey data.
    survey_results = CONFIG["survey_results"]
    honey_money_df = pd.read_excel(survey_results, sheet_name='honey_prices')

    # Cost data.
    migrations_fn = CONFIG["migrations_processed"]
    df_migrations = pd.read_excel(migrations_fn, sheet_name='fuel prices included 5km')

    # Generate travel data.
    travel = np.arange(0, 600, 20)

    # Premise 1: travelling with personal car with 10 hives.
    fuel_10_hives = linear(10, df_consumption.loc[0, "k_linear"], df_consumption.loc[0, "intercept_linear"])
    fuel_10_hives_unc = linear(10, df_consumption.loc[0, "k_unc_lin"], df_consumption.loc[0, "intercept_unc_lin"])
    fuel_10_df = pd.DataFrame({"Distance": travel, "Fuel consumption": travel*fuel_10_hives})

    # Premise 2: travelling with personal car with 20 hives in 2022.
    fuel_20_hives = linear(20, df_consumption.loc[0, "k_linear"], df_consumption.loc[0, "intercept_linear"])
    fuel_20_hives_unc = linear(20, df_consumption.loc[0, "k_unc_lin"], df_consumption.loc[0, "intercept_unc_lin"])
    cost_20_df = pd.DataFrame({"Distance": travel, "Fuel consumption": travel * fuel_20_hives})

        
    df_migrations["year"] = df_migrations["year"].astype(str)

   
    # Cost per hive moved per kilometer traveled.
    fig_cost_per_hive_per_km = plt.figure(figsize=(8, 4))
    a_cost_per_hive_per_km = fig_cost_per_hive_per_km.add_axes((0.15, 0.15, 0.80, 0.75))

    sns.lineplot(
        data=df_migrations.loc[df_migrations["FAMILY_MOVE"] == 8],
        x="year",
        y="cost per hive moved per kilometer",
        color="lightblue",
        ax=a_cost_per_hive_per_km, 
        label="car, 8 hives", 
        linestyle="solid"
    )

    sns.lineplot(
        data=df_migrations.loc[df_migrations["FAMILY_MOVE"] == 10], 
        x="year", 
        y="cost per hive moved per kilometer",
        color="dodgerblue", 
        ax=a_cost_per_hive_per_km, 
        label="car, 10 hives", 
        linestyle="dotted"
    )
    
    sns.lineplot(
        data=df_migrations.loc[df_migrations["FAMILY_MOVE"] == 20], 
        x="year", 
        y="cost per hive moved per kilometer",
        color="blue", 
        ax=a_cost_per_hive_per_km, 
        label="car, 20 hives", 
        linestyle="dashed"
    )
    
    sns.lineplot(
        data=df_migrations.loc[df_migrations["FAMILY_MOVE"] == 24], 
        x="year", 
        y="cost per hive moved per kilometer",
        color="royalblue", 
        ax=a_cost_per_hive_per_km, 
        label="car, 24 hives", 
        linestyle="dashdot"
    )
    
    sns.lineplot(
        data=df_migrations.loc[df_migrations["FAMILY_MOVE"] == 28], 
        x="year", 
        y="cost per hive moved per kilometer",
        color="darkblue", 
        ax=a_cost_per_hive_per_km, 
        label="car, 28 hives", 
        linestyle="solid"
    )
    
    sns.lineplot(
        data=df_migrations.loc[df_migrations["FAMILY_MOVE"] == 40], 
        x="year", 
        y="cost per hive moved per kilometer",
        color="orange", 
        ax=a_cost_per_hive_per_km, 
        label="truck, 40 hives", 
        linestyle="dotted"
    )
    
    sns.lineplot(
        data=df_migrations.loc[df_migrations["FAMILY_MOVE"] == 60], 
        x="year", 
        y="cost per hive moved per kilometer",
        color="gold", 
        ax=a_cost_per_hive_per_km, 
        label="truck, 60 hives", 
        linestyle="dashed"
    )
    
    sns.lineplot(
        data=df_migrations.loc[df_migrations["FAMILY_MOVE"] == 72], 
        x="year", 
        y="cost per hive moved per kilometer",
        color="lime", 
        ax=a_cost_per_hive_per_km, 
        label="truck, 72 hives", 
        linestyle="dashdot"
    )
    
    a_cost_per_hive_per_km.set_xticklabels(
        ["2014", "2015", "2016", "2017", "2018", "2019", "2020", "2021", "2022"],
        fontsize=15
    )
    
    a_cost_per_hive_per_km.set_xlabel("Year", fontsize=15)
    a_cost_per_hive_per_km.set_ylabel("Cost of migration [€ / hive / km]", fontsize=15)
    a_cost_per_hive_per_km.tick_params(labelsize=15, axis="both")
    
    ### fix the legend
    h, l = a_cost_per_hive_per_km.get_legend_handles_labels()
    a_cost_per_hive_per_km.legend_.remove()
    fig_cost_per_hive_per_km.legend(h, l, ncol=2, loc="upper center", bbox_to_anchor=(0.55, 0.9))


    fig_cost_per_hive_per_km.savefig(f'{CONFIG["cost_per_hive_per_km_fig"]}.pdf')

    # Write stats.
    cost_df = df_migrations.groupby(["FAMILY_MOVE", "year"])["cost per hive moved per kilometer"].describe().reset_index()
    writer = pd.ExcelWriter(CONFIG["migrations_travel_costs"], engine='openpyxl')
    cost_df.to_excel(writer, sheet_name='cost per hive per kilometer', index=False)
    writer.close()

    pass
