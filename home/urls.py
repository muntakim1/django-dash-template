from django.urls import path,include
from . import views
from .dash_apps import rateapp

urlpatterns = [
    path('',views.home,name="home"),

]
