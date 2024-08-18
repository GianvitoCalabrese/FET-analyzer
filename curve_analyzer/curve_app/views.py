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
        # file lo ricevi dalla chiamata
        file = request.FILES['data']
        x_column = request.POST.get('x_column', 'x')  # Ottieni il nome della colonna x dal POST
        y_column = request.POST.get('y_column', 'y')  # Ottieni il nome della colonna y dal POST

        print(f'Colonna x selezionata: {file}')  # Debugging
        print(f'Colonna x selezionata: {x_column}')  # Debugging
        print(f'Colonna y selezionata: {y_column}')  # Debugging

        lines = file.readlines()
        # Unire tutti i byte in una sola stringa
        data_str = b''.join(lines).decode('utf-8')
        # Creiamo un oggetto StringIO
        data = io.StringIO(data_str)
        # Leggiamo i dati in un DataFrame
        df = pd.read_csv(data, sep='\t')
        # Selezioniamo tutte le colonne di tipo object
        cols_to_convert = df.select_dtypes(include='object').columns

        # Convertiamo queste colonne in float
        df[cols_to_convert] = df[cols_to_convert].apply(pd.to_numeric, errors='coerce')
        #df.columns = df.columns.str.strip()
        print(df.dtypes)

        print('Colonne nel DataFrame:', df.columns)  # Debugging
        # Verifica le colonne presenti nel DataFrame
        #qua interessante perche'se hai l'errore vai nel return ed esci dalla funzione madre...

        #if x_column not in df.columns or y_column not in df.columns:
        #    return JsonResponse({'error': f'Il file CSV deve contenere le colonne {x_column} e {y_column}'})
        # print(df)
        vds_list = np.unique([row[0] for row in df.itertuples(index=False, name=None) if not pd.isnull(row[0])])

        print('vds list qua', vds_list)
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
            
            # Plotta i risultati
            plt.plot(x_clean, derivative_clean, label=z, linewidth=0.5)
            
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
                result_data = scipy.signal.convolve(yy_1, window / window.sum(), mode='same')
                print(result_data)
                
                # Plotta o salva il risultato finale
                plt.plot(xx_1, result_data, label=f'{z} convoluted', linewidth=0.5)
            else:
                print(f"Not enough data points for interpolation for VDS = {z}")
        return JsonResponse({'result': result_data})
    else:
        return JsonResponse({'error': 'Metodo non consentito'})
