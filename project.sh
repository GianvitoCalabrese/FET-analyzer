#!/bin/bash

# Portable launcher: prefer conda if available, otherwise use a local venv
set -euo pipefail

# Config: desired Conda env name (change if needed)
CONDA_ENV_NAME="python31113"

function use_conda() {
    # Try to locate conda. Prefer conda in PATH, otherwise try common Windows path.
    if command -v conda >/dev/null 2>&1; then
        return 0
    fi
    if [ -f "$HOME/anaconda3/etc/profile.d/conda.sh" ]; then
        source "$HOME/anaconda3/etc/profile.d/conda.sh"
        return 0
    fi
    if [ -f "/c/Users/tele1/anaconda3/etc/profile.d/conda.sh" ]; then
        source "/c/Users/tele1/anaconda3/etc/profile.d/conda.sh"
        return 0
    fi
    return 1
}

if use_conda; then
    echo "Conda found — using conda flow"
    # If the env exists, activate it; otherwise create it and install basic deps
    if conda info --envs | awk '{print $1}' | grep -qx "$CONDA_ENV_NAME"; then
        conda activate "$CONDA_ENV_NAME"
    else
        echo "Conda env '$CONDA_ENV_NAME' not found. Creating..."
        conda create -y -n "$CONDA_ENV_NAME" python=3.11
        conda activate "$CONDA_ENV_NAME"
        pip install --upgrade pip
        # install minimal deps; keep packages lightweight
        pip install django numpy scipy matplotlib opencv-python pandas
    fi
else
    echo "Conda not found — falling back to venv"
    # Create and activate a local venv in repo root
    PY=python3
    if ! command -v $PY >/dev/null 2>&1; then
        PY=python
    fi
    ${PY} -m venv .venv
    # Shell-specific activation
    if [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate
    elif [ -f ".venv/Scripts/activate" ]; then
        # Git Bash on Windows may have this layout
        source .venv/Scripts/activate
    else
        echo "Could not find venv activation script. Activate .venv manually and re-run."
        exit 1
    fi
    pip install --upgrade pip
    if [ -f requirements.txt ]; then
        pip install -r requirements.txt
    else
        pip install django numpy scipy matplotlib opencv-python pandas
    fi
fi

echo "✅ Checking if Django is installed..."
if ! python -c "import django" &> /dev/null; then
        echo "⚠️ Django not found after environment setup. Installing via pip..."
        pip install django
else
        echo "✅ Django is already installed."
fi

echo "Proceeding to Django project commands"
cd curve_analyzer

python manage.py makemigrations || true
python manage.py migrate
#run --noreload to allow pdb
#python manage.py runserver --noreload
python manage.py runserver