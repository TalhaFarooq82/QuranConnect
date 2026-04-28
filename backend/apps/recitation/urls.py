from django.urls import path
from .views import recitation_page

urlpatterns = [
    path('tajweed/', recitation_page,name = 'recitation_page')
]
