from django.urls import path
from . import views

urlpatterns = [
    path("route/", views.get_fuel_route, name="get_fuel_route"),
    path("map/", views.map_view, name="map_view"),
]