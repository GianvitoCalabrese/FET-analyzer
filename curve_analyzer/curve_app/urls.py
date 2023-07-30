from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('analyze_data/', views.analyze_data, name='analyze_data'),
]
