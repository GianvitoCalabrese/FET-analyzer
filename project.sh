#!/bin/bash

cd curve_analyzer
python manage.py migrate
python manage.py runserver


