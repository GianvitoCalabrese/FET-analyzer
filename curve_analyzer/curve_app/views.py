from django.shortcuts import render
from django.http import JsonResponse
import pandas as pd
import io
import numpy as np
import scipy.interpolate as interp
import scipy.signal
import matplotlib.pyplot as plt

w = 5*10**-6  # channel_width

def index(request):
    return render(request, 'index.html')

def analyze_data(request):
    if request.method == 'POST':
        if 'data' not in request.FILES:
            return JsonResponse({'error': 'File non ricevuto'})
        
        file = request.FILES['data']
        x_column = request.POST.get('x_column', 'x')  # Ottieni il nome della colonna x dal POST
        y_column = request.POST.get('y_column', 'y')  # Ottieni il nome della colonna y dal POST

        # Leggi il file e convertilo in un DataFrame
        data_str = b''.join(file.readlines()).decode('utf-8')
        data = io.StringIO(data_str)
        df = pd.read_csv(data, sep='\t')
        
        # Converte le colonne di tipo object in float
        cols_to_convert = df.select_dtypes(include='object').columns
        df[cols_to_convert] = df[cols_to_convert].apply(pd.to_numeric, errors='coerce')
        
        vds_list = np.unique(df['VDS'].dropna().values)

        result_data = {
            'x_values': [],
            'y_values': []
        }

        for z in vds_list:
            x = df.loc[df['VDS'] == z, x_column].values
            y = df.loc[df['VDS'] == z, y_column].values
            
            # Calcola le differenze
            dx = np.diff(x)
            dy = np.diff(y)
            
            # Gestisci le divisioni per zero
            with np.errstate(divide='ignore', invalid='ignore'):
                derivative = np.where(dx != 0, dy / (dx * w), np.nan)
            
            # Rimuovi eventuali NaN e infiniti
            mask = ~np.isnan(derivative) & np.isfinite(derivative)
            x_clean = x[:-1][mask]
            derivative_clean = derivative[mask]
            
            # Rimozione dei duplicati
            x_clean, unique_indices = np.unique(x_clean, return_index=True)
            derivative_clean = derivative_clean[unique_indices]
            
            # Interpolazione
            if len(x_clean) > 1:  # Assicurati di avere abbastanza punti per l'interpolazione
                f = interp.interp1d(x_clean, derivative_clean, fill_value="extrapolate", kind='slinear')
                xx_0 = np.linspace(min(x_clean), max(x_clean), 5000)
                yy_0 = f(xx_0)
                
                # Rimuovi eventuali NaN o infiniti dall'interpolazione
                valid_mask = np.isfinite(yy_0)
                xx_1 = xx_0[valid_mask]
                yy_1 = yy_0[valid_mask]
                
                # Convoluzione
                window = scipy.signal.gaussian(200, 60)
                yy_smooth = scipy.signal.convolve(yy_1, window / window.sum(), mode='same')
                
                # Aggiungi i risultati alle liste x_values e y_values
                result_data['x_values'].extend(xx_1.tolist())
                result_data['y_values'].extend(yy_smooth.tolist())
                
            else:
                print(f"Not enough data points for interpolation for VDS = {z}")
        
        return JsonResponse({'result': result_data})
    else:
        return JsonResponse({'error': 'Metodo non consentito'})
