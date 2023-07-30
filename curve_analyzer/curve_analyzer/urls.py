# your_project_name/urls.py

from django.urls import path, include

urlpatterns = [
    # Add your app's URL patterns here
    path('', include('curve_app.urls')),
]
