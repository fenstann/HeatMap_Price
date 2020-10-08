from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('idwdata/', views.SellListMap.as_view()),
    path('getcities/', views.CityList.as_view()),
    path('distance/', views.ListDistance.as_view(),name = 'listDistance'),
]
