#!/bin/bash

# Activate the Anaconda environment
# Please use python >= 3.11
source C:/Users/tele1/anaconda3/etc/profile.d/conda.sh
conda activate python31113

echo "✅ Checking if Django is installed..."
if ! python -c "import django" &> /dev/null; then
    echo "⚠️ Django not found, installing..."
    pip install django
else
    echo "✅ Django is already installed."
fi

# Add additional checks for other libraries
REQUIRED_LIBS=("numpy" "scipy" "matplotlib" "opencv-python")

for LIB in "${REQUIRED_LIBS[@]}"; do
    echo "✅ Checking if $LIB is installed..."
    python -c "import $LIB" 2>/dev/null
    if [ $? -ne 0 ]; then
        echo "⚠️ $LIB not found, installing..."
        pip install $LIB
    else
        echo "✅ $LIB is already installed."
    fi
done

# Proceed to Django project commands
cd curve_analyzer

python manage.py makemigrations
python manage.py migrate
python manage.py runserver