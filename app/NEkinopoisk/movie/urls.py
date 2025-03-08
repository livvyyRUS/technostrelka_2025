from django.urls import path
from . import views

urlpatterns = [
    path('<int:id_film>/', views.movie, name='index')
]
