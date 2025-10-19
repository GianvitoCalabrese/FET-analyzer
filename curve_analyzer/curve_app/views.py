from django.shortcuts import render 
from django.http import JsonResponse
import pandas as pd
import io
import numpy as np
import scipy.interpolate as interp
import scipy.signal

w = 5e-6  # channel_width

def index(request):
    return render(request, 'index.html')

def analyze_data(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Metodo non consentito'})

    if 'data' not in request.FILES:
        return JsonResponse({'error': 'File non ricevuto'})

    file = request.FILES['data']
    x_column = (request.POST.get('x_column', '') or '').strip()
    y_column = (request.POST.get('y_column', '') or '').strip()

    # --- Read the file into a DataFrame
    data_str = b''.join(file.readlines()).decode('utf-8', errors='replace')
    data = io.StringIO(data_str)
    try:
        df = pd.read_csv(data, sep='\t')
    except Exception as e:
        return JsonResponse({'error': f'Errore lettura file: {str(e)}'})

    df.columns = df.columns.str.strip()

    # Validate selected columns
    if x_column not in df.columns or y_column not in df.columns:
        return JsonResponse({
            'error': f"Colonna non trovata: '{x_column}' o '{y_column}'. Colonne disponibili: {', '.join(df.columns)}"
        })

    # Clean up data types
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Check for required grouping column
    if 'VDS' not in df.columns:
        return JsonResponse({
            'error': "Colonna 'VDS' mancante dal file. Colonne disponibili: " + ', '.join(df.columns)
        })

    vds_list = np.unique(df['VDS'].dropna().values)
    result_data = {
        'x_values': [],
        'y_values': []
    }
    warnings = []

    max_points_per_sweep = 200  # <= Change as needed

    for z in vds_list:
        x = df.loc[df['VDS'] == z, x_column].values
        y = df.loc[df['VDS'] == z, y_column].values

        # Remove NaN and ensure there are at least two unique x points
        mask_valid = (~np.isnan(x)) & (~np.isnan(y))
        x = x[mask_valid]
        y = y[mask_valid]
        if len(np.unique(x)) < 2:
            warnings.append(f"VDS={z}: dati insufficienti ({len(x)} punti validi)")
            continue

        dx = np.diff(x)
        dy = np.diff(y)
        with np.errstate(divide='ignore', invalid='ignore'):
            derivative = np.where(dx != 0, dy / (dx * w), np.nan)
        mask = ~np.isnan(derivative) & np.isfinite(derivative)
        x_clean = x[:-1][mask]
        derivative_clean = derivative[mask]
        if len(x_clean) < 2:
            warnings.append(f"VDS={z}: dati insufficienti per interpolazione dopo il filtraggio")
            continue

        # Remove duplicates
        x_clean, unique_indices = np.unique(x_clean, return_index=True)
        derivative_clean = derivative_clean[unique_indices]
        if len(x_clean) < 2:
            warnings.append(f"VDS={z}: valori x duplicati, nessuna interpolazione possibile")
            continue

        try:
            f = interp.interp1d(x_clean, derivative_clean, fill_value="extrapolate", kind='slinear')
            xx_0 = np.linspace(min(x_clean), max(x_clean), 5000)
            yy_0 = f(xx_0)
            valid_mask = np.isfinite(yy_0)
            xx_1 = xx_0[valid_mask]
            yy_1 = yy_0[valid_mask]
            window = scipy.signal.windows.gaussian(200, 60)
            yy_smooth = scipy.signal.convolve(yy_1, window / window.sum(), mode='same')

            # ---- DOWNSAMPLE BEFORE SENDING TO FRONTEND! ----
            if len(xx_1) > max_points_per_sweep:
                idx = np.round(np.linspace(0, len(xx_1) - 1, max_points_per_sweep)).astype(int)
                xx_1_down = xx_1[idx]
                yy_smooth_down = yy_smooth[idx]
            else:
                xx_1_down = xx_1
                yy_smooth_down = yy_smooth

            result_data['x_values'].extend(xx_1_down.tolist())
            result_data['y_values'].extend(yy_smooth_down.tolist())

        except Exception as ex:
            warnings.append(f"Errore durante l'interpolazione per VDS={z}: {str(ex)}")

    # Always return at least an empty result (not error), plus warnings if any
    return JsonResponse({'result': result_data, 'warnings': warnings})
