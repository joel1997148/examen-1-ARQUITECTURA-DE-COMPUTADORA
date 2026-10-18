from django.urls import path

from . import views

app_name = "representacion"

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("numero/", views.convertir_numero, name="numero"),
    path("texto/", views.analizar_texto, name="texto"),
    path("salud/", views.salud, name="salud"),
]
