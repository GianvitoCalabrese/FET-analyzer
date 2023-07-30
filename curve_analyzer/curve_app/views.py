# views.py
from django.shortcuts import render
from django.http import JsonResponse
import pandas as pd
from scipy import interpolate

def index(request):
    return render(request, 'index.html')

def analyze_data(request):
    if request.method == 'POST':
        # Controlla se il file è stato correttamente ricevuto
        if 'data' not in request.FILES:
            return JsonResponse({'error': 'File non ricevuto'})

        file = request.FILES['data']

        try:
            # Leggi il file CSV con pandas
            df = pd.read_csv(file)

            # Verifica le colonne presenti nel DataFrame
            if 'x' not in df.columns or 'y' not in df.columns:
                return JsonResponse({'error': 'Il file CSV deve contenere colonne x e y'})

            # Esegui l'interpolazione
            x = df['x']
            y = df['y']
            f = interpolate.interp1d(x, y, kind='linear')  # Cambia 'linear' con il tipo di interpolazione desiderato
            interpolated_x = x  # Puoi usare gli stessi valori x del CSV come punti interpolati
            interpolated_y = f(interpolated_x)  # Esegui l'interpolazione

            # Puoi fare ulteriori elaborazioni sui dati interpolati se necessario
            # Ad esempio, puoi calcolare medie, massimi, minimi, ecc.

            # Restituisci i risultati dell'interpolazione come JSON
            result_data = {'x_values': interpolated_x.tolist(), 'y_values': interpolated_y.tolist()}
            return JsonResponse({'result': result_data})

        except Exception as e:
            return JsonResponse({'error': 'Errore durante l\'analisi dei dati: {}'.format(str(e))})

    else:
        return JsonResponse({'error': 'Metodo non consentito'})
