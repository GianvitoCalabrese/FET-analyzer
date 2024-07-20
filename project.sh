#!/bin/bash

# Attiva l'ambiente Anaconda
source C:/Users/tele1/anaconda3/etc/profile.d/conda.sh
conda activate python3115

cd curve_analyzer
python manage.py makemigrations
python manage.py migrate
python manage.py runserver


