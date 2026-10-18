from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_http_methods

from .forms import NumeroForm, TextoForm

PLANTILLA = "representacion/index.html"


def _render(request, numero_form, texto_form, *, resultado=None, caracteres=None, status=200):
    return render(request, PLANTILLA, {
        "numero_form": numero_form,
        "texto_form": texto_form,
        "resultado": resultado,
        "caracteres": caracteres,
    }, status=status)


@require_GET
def inicio(request: HttpRequest) -> HttpResponse:
    return _render(request, NumeroForm(), TextoForm())


@require_http_methods(["GET", "POST"])
def convertir_numero(request: HttpRequest) -> HttpResponse:
    form = NumeroForm(request.POST) if request.method == "POST" else NumeroForm()
    if request.method == "POST" and form.is_valid():
        return _render(request, form, TextoForm(), resultado=form.cleaned_data["resultado"])
    # 422: la petición llegó bien pero los datos no son procesables
    return _render(request, form, TextoForm(), status=422 if request.method == "POST" else 200)


@require_http_methods(["GET", "POST"])
def analizar_texto(request: HttpRequest) -> HttpResponse:
    form = TextoForm(request.POST) if request.method == "POST" else TextoForm()
    if request.method == "POST" and form.is_valid():
        return _render(request, NumeroForm(), form, caracteres=form.cleaned_data["caracteres"])
    return _render(request, NumeroForm(), form, status=422 if request.method == "POST" else 200)


@require_GET
def salud(request: HttpRequest) -> JsonResponse:
    """Endpoint ligero para el HEALTHCHECK del contenedor."""
    return JsonResponse({"estado": "ok"})
