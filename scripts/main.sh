#!/usr/bin/env bash

# Run all pre-processing and processing scripts. 
#
# Input and output paths/filenames are read from config.yaml. This also includes
# the url where the local installation of graphhopper routing engine is 
# accessible.

# Assumes that the conad env exists. See requirements.txt for specifications.
#
# Conda activate is not recommended for non-interactive sessions. 
# Consider using "conda run" instead..

eval "$(conda shell.bash hook)"
conda activate migrations

python preprocessing_1.py &&
echo "preprocessing_1 done" &&

python preprocessing_2.py &&
echo "preprocessing_2 done" &&

python preprocessing_3.py &&
echo "preprocessing-3 done" &&

python model_of_travel_costs.py &&
echo "model_of_travel_costs done" &&

python migrations_fuel_calculations.py &&
echo "fuel_calculations done" &&

python "migrations_stats.py" &&
echo "migrations_stats done"
