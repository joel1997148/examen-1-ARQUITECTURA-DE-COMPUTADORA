from django import forms

from . import services


class NumeroForm(forms.Form):
    """Formulario 1: número + base de origen."""

    numero = forms.CharField(
        label="Número",
        required=False,  # el mensaje de vacío lo da la capa de servicios
        max_length=32,
        widget=forms.TextInput(attrs={
            "autocomplete": "off", "spellcheck": "false",
            "placeholder": "Ej.: 1F4, 255, 777, 1010",
        }),
        error_messages={"max_length": "El número es demasiado largo (máximo 32 dígitos)."},
    )
    base = forms.TypedChoiceField(
        label="Base de origen",
        choices=[(b, f"{b} · {services.NOMBRE_BASE[b]}") for b in services.BASES_PERMITIDAS],
        coerce=int,
        initial=10,
        error_messages={"invalid_choice": "La base seleccionada no es válida. Elija 2, 8, 10 o 16."},
    )

    def clean(self):
        datos = super().clean()
        if self.errors:
            return datos
        try:
            valor = services.parsear_numero(datos.get("numero"), datos["base"])
        except services.ErrorDeValidacion as e:
            self.add_error("numero", str(e))
        else:
            datos["resultado"] = services.convertir(valor)
        return datos


class TextoForm(forms.Form):
    """Formulario 2: texto de hasta 20 caracteres."""

    texto = forms.CharField(
        label="Texto",
        required=False,
        strip=False,  # los espacios también son caracteres a analizar
        widget=forms.TextInput(attrs={
            "maxlength": services.MAX_CARACTERES, "autocomplete": "off",
            "placeholder": "Ej.: Año, ñandú, €uro",
        }),
    )

    def clean(self):
        datos = super().clean()
        try:
            datos["caracteres"] = services.analizar_texto(datos.get("texto"))
        except services.ErrorDeValidacion as e:
            self.add_error("texto", str(e))
        return datos
