from django.shortcuts import render
from django.http import JsonResponse
import pandas as pd
from scipy import interpolate
import io

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
        print(df.dtypes)

        print('Colonne nel DataFrame:', df.columns)  # Debugging
        # Verifica le colonne presenti nel DataFrame
        #qua interessante perche'se hai l'errore vai nel return ed esci dalla funzione madre...

        #if x_column not in df.columns or y_column not in df.columns:
        #    return JsonResponse({'error': f'Il file CSV deve contenere le colonne {x_column} e {y_column}'})

        

        # Esegui l'interpolazione
        x = df[x_column]
        print(x)
        y = df[y_column]
        f = interpolate.interp1d(x, y, kind='linear')  # Cambia 'linear' con il tipo di interpolazione desiderato
        interpolated_x = x  # Puoi usare gli stessi valori x del CSV come punti interpolati
        interpolated_y = f(interpolated_x)  # Esegui l'interpolazione

        # Restituisci i risultati dell'interpolazione come JSON
        result_data = {'x_values': interpolated_x.tolist(), 'y_values': interpolated_y.tolist()}
        print('interpolazione', result_data)
        return JsonResponse({'result': result_data})



    else:
        return JsonResponse({'error': 'Metodo non consentito'})
