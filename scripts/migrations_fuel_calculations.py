#!/usr/bin/env python3
""" 4th step

Preprocessing of migration data by adding fuel prices and fuel consumption to 
every journey:

    * Adding toll where applicatble (> 28 hives)
    * Add also the percentage travelled on motorway
    * Add also cost per hive move, for individual move
    * Inserts yearly recommended honey price

"""
__author__ = "janez presern, anja pavlin, andraz marinc"



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
from PIL import Image


with open("config.yaml") as f:
    CONFIG = yaml.load(f, Loader=yaml.FullLoader)


def fit_the_data (df, fits):

    df = df[["towing vehicle", "migratory unit", "no of colonies", "fuel consumption", "fuel consumption [L / km]"]]
    df = df.dropna()

    """ get the array """
    arr = df[["no of colonies", "fuel consumption [L / km]"]].values

    x = np.linspace(df["no of colonies"].min(), df["no of colonies"].max(), 100)
    """ fit exp"""
    popt_e, pcov_e = curve_fit(rise_exp2, arr[:, 0], arr[:, 1], maxfev=10000, bounds=([0.001, 0, 0], [500.0, 50, 10]))
    y_e = rise_exp2(x, popt_e[0], popt_e[1], popt_e[2])
    y_pred_e = rise_exp2(arr[:, 0], popt_e[0], popt_e[1], popt_e[2])

    """ fit lin """
    popt_l, pcov_l = curve_fit(linear, arr[:, 0], arr[:, 1], maxfev=10000, bounds=([0.00, 0], [5, 100]))

    y_l = linear(x, popt_l[0], popt_l[1])
    y_pred_l = linear(arr[:, 0], popt_l[0], popt_l[1])

    """ fit LMFIT """
    e_model = Model(rise_exp2)
    e_pars = e_model.make_params(k=popt_e[0], top=popt_e[1], offset=popt_e[2])
    e_pars['k'].max = 500.0
    e_pars['k'].min = 0.001
    e_pars['top'].max = 100
    e_pars['top'].min = 0
    e_pars['offset'].max = 10
    e_pars['offset'].min = 0
    e_res = e_model.fit(arr[:, 1], e_pars, x=arr[:, 0])

    """ uncertanities exponential """
    k_e, top_e, offset_e = unc.correlated_values(popt_e, pcov_e)
    py_e = unp_rise_exp2(x, k_e, top_e, offset_e)
    nom_e = unp.nominal_values(py_e)
    std_e = unp.std_devs(py_e)

    """ uncertanities linear """
    k_l, intercept_l = unc.correlated_values(popt_l, pcov_l)
    py_l = linear(x, k_l, intercept_l)
    nom_l = unp.nominal_values(py_l)
    std_l = unp.std_devs(py_l)

    """ aic score exp lin """
    aic_score_exp = aic.aic(arr[:, 1], y_pred_e, 3)
    aic_score_lin = aic.aic(arr[:, 1], y_pred_l, 2)

    """ compute R2 """
    r_2_e = r_square(arr[:, 0], arr[:, 1], popt_e, rise_exp2)
    r_2_l = r_square(arr[:, 0], arr[:, 1], popt_l, linear)

    """ stdev on parameter use"""
    perr_e = np.sqrt(np.diag(pcov_e))
    perr_l = np.sqrt(np.diag(pcov_l))


    """ store the hit """
    fits.loc[0, "what"] = "fuel consumption"
    fits.loc[0, "r_2_l"] = r_2_l
    fits.loc[0, "k_linear"] = popt_l[0]
    fits.loc[0, "intercept_linear"] = popt_l[1]
    fits.loc[0, "k_unc_lin"] = k_l
    fits.loc[0, "intercept_unc_lin"] = intercept_l
    fits.loc[0, "aic_lin"] = aic_score_lin

    fits.loc[0, "r_2_e"] = r_2_e
    fits.loc[0, "k_e"] = popt_e[0]
    fits.loc[0, "top_e"] = popt_e[1]
    fits.loc[0, "offset_e"] = popt_e[2]
    fits.loc[0, "k_unc_e"] = k_e
    fits.loc[0, "top_unc_e"] = top_e
    fits.loc[0, "offset_unc_e"] = offset_e
    fits.loc[0, "aic_exp"] = aic_score_exp

    """ draw """
    f = plt.figure(figsize=(170/25.4, 143/25.4))
    a = f.add_subplot(111)

    a.fill_between(x, nom_l*100 - 2 * std_l*100, nom_l*100 + 2 * std_l*100, color="k", alpha=0.25)
    a.plot(x, y_l*100, color="k", linestyle="--", linewidth=3)
    sns.scatterplot(df, x="no of colonies", y="fuel consumption", hue="towing vehicle")
    a.set_ylim(0, 35)

    """ cosmetics """
    a.tick_params(axis='both', which='major', labelsize=15)
    a.set_xlabel("No of colonies", fontsize=15)
    a.set_ylabel("Fuel consumption [L/100 km]", fontsize=15)
    a.legend(fontsize=15)

    a.text(90, 27, '$R^2$ = '  + str(np.round(r_2_l, 2)), rotation=30, fontsize=15)
    f.savefig(f'{CONFIG['fuel_consumption_calibration_fig']}.pdf')
    
    # Convert image to CMYK for publication.
    image = Image.open(f'{CONFIG['fuel_consumption_calibration_fig']}.pdf')
    cmyk_image = image.convert('CMYK')
    cmyk_image.save(f'{CONFIG['fuel_consumption_calibration_fig']}_CMYK.pdf')

    
    writer = pd.ExcelWriter(CONFIG['fuel_calibrations'])
    fits.to_excel(writer, sheet_name="fuel_calibration", index=False)
    writer.close()

    pass

    return fits

if __name__ == "__main__":



    """ fuel consumption """
    consumption_fn = CONFIG['survey_results']
    df_consumption = pd.read_excel(consumption_fn, sheet_name='transportation')
    df_honey_price = pd.read_excel(consumption_fn, sheet_name='honey_prices')

    """ migration data """
    migrations_fn = CONFIG['migrations_processed']
    df_migrations = pd.read_excel(migrations_fn, sheet_name='migrations distances_5 cutoff')

    """ fuel data """
    fuel_fn = CONFIG['fuel_prices']
    df_fuel = pd.read_excel(fuel_fn, sheet_name='diesel')

    """ toll data """
    df_toll = pd.read_excel(fuel_fn, sheet_name='toll')

    """ remove fuel data for 2023 """
    df_fuel = df_fuel.loc[df_fuel["start_date"] < "2023-01-01"]
    df_migrations = df_migrations.loc[df_migrations["DATE_MOVE"] < "2023-01-01"]

    """ assign fuel prices to date of migration """
    for i, row in df_fuel.iterrows():
        df_migrations.loc[(df_migrations.DATE_MOVE >= row.start_date) & (df_migrations.DATE_MOVE <= row.end_date), "Fuel price"] = row.price

    """ fit equation to fuel consumption from survey """
    fits = fit_the_data(df_consumption, pd.DataFrame())

    """ using fit calcualte fuel consumption for every travel; don't forget to divide the consumption with 100 """
    df_migrations["fuel consumption per km unc"] = df_migrations.FAMILY_MOVE.apply(func=linear, args=(fits.iloc[0].k_unc_lin, fits.iloc[0].intercept_unc_lin))
    df_migrations["fuel consumption per km"] = df_migrations.FAMILY_MOVE.apply(func=linear, args=(fits.iloc[0].k_linear, fits.iloc[0].intercept_linear))

    """ calculate fuel costs for every travel"""
    df_migrations["fuel consumption per travel"] = df_migrations["fuel consumption per km"] * df_migrations["travel_distances"]
    df_migrations["fuel paid"] = df_migrations["fuel consumption per travel"] * df_migrations["Fuel price"]

    """ assign toll pracies to date of migration """
    for j, toll_row in df_toll.iterrows():
        df_migrations.loc[(df_migrations.DATE_MOVE >= toll_row.start_date) & (df_migrations.DATE_MOVE <= toll_row.end_date) & (df_migrations.FAMILY_MOVE > 28), "Euro 0 - 2"] = toll_row["Euro 0 - 2"]
        df_migrations.loc[(df_migrations.DATE_MOVE >= toll_row.start_date) & (df_migrations.DATE_MOVE <= toll_row.end_date) & (
                        df_migrations.FAMILY_MOVE > 28), "Euro 6, EEV"] = toll_row["Euro 6, EEV"]
    df_migrations["toll Euro 0 - 3"] = np.nan
    df_migrations["toll Euro 6, EEV"] = np.nan
    df_migrations["toll Euro 0 - 2"] = df_migrations["Euro 0 - 2"] * df_migrations["motorway"]
    df_migrations["toll Euro 6, EEV"] = df_migrations["Euro 6, EEV"] * df_migrations["motorway"]

    """ insert zeros """
    df_migrations["toll Euro 0 - 2"].fillna(0, inplace=True)
    df_migrations["toll Euro 6, EEV"].fillna(0, inplace=True)

    """ assign percantage travelled on motorways """
    df_migrations["percentage motorway"] = df_migrations["motorway"] / df_migrations["travel_distances"]

    """ assign cost per hive moved """
    df_migrations["cost per hive moved"] = (df_migrations["fuel paid"] + df_migrations["toll Euro 0 - 2"]) / df_migrations["FAMILY_MOVE"]

    """ assign cost per hive moved per kilometer travelled """
    df_migrations["cost per hive moved per kilometer"] = df_migrations["cost per hive moved"]  / df_migrations["travel_distances"]

    """ insert yearly recommended honey price """
    B = df_honey_price.set_index("year")[["recommended retail price [kg]"]]
    df_migrations["recommended retail honey price [kg]"] = df_migrations["year"].map(B["recommended retail price [kg]"])


    """ write the df """
    writer = pd.ExcelWriter(CONFIG['migrations_processed'], engine='openpyxl', mode='a', if_sheet_exists='replace')
    df_migrations.to_excel(writer, sheet_name="fuel prices included 5km", index=False)
    writer.close()

    pass
