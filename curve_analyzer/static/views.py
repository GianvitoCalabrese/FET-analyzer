from django.shortcuts import render, redirect
from django.http import JsonResponse
from .models import CurveData

def index(request):
    return render(request, 'index.html')

def analyze_data(request):
    if request.method == 'POST':
        data = request.POST.get('data')
        # Qui puoi elaborare i dati delle curve e ottenere il risultato dell'analisi
        # Ad esempio:
        # analysis_result = perform_analysis(data)

        # Nel nostro esempio, solo inviamo di nuovo i dati ricevuti come risultato per la visualizzazione
        analysis_result = data
        return JsonResponse({'result': analysis_result})
    else:
        return JsonResponse({'error': 'Metodo non consentito'})
