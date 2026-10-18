"""Pruebas de integración: URLs, formularios, plantillas y códigos HTTP."""

from django.test import SimpleTestCase
from django.urls import reverse


class VistasTests(SimpleTestCase):
    def test_inicio_muestra_ambos_formularios(self):
        r = self.client.get(reverse("representacion:inicio"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'name="numero"')
        self.assertContains(r, 'name="texto"')
        self.assertContains(r, "csrfmiddlewaretoken")

    def test_conversion_valida_renderiza_resultado(self):
        r = self.client.post(reverse("representacion:numero"), {"numero": "1F4", "base": "16"})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "00000001 11110100")
        self.assertContains(r, "764")
        self.assertEqual(r.context["resultado"].bytes_necesarios, 2)

    def test_error_de_base_responde_422_con_mensaje(self):
        r = self.client.post(reverse("representacion:numero"), {"numero": "102", "base": "2"})
        self.assertEqual(r.status_code, 422)
        self.assertContains(r, "Dígitos inválidos para la base 2", status_code=422)
        self.assertIsNone(r.context["resultado"])

    def test_error_de_rango_responde_422(self):
        r = self.client.post(reverse("representacion:numero"), {"numero": "70000", "base": "10"})
        self.assertContains(r, "fuera del rango permitido", status_code=422)

    def test_base_manipulada(self):
        r = self.client.post(reverse("representacion:numero"), {"numero": "10", "base": "7"})
        self.assertContains(r, "La base seleccionada no es válida", status_code=422)

    def test_utf8_con_enie_en_la_pagina(self):
        r = self.client.post(reverse("representacion:texto"), {"texto": "Año"})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "U+00F1")
        self.assertContains(r, "C3 B1")

    def test_texto_largo_responde_422(self):
        r = self.client.post(reverse("representacion:texto"), {"texto": "a" * 21})
        self.assertContains(r, "máximo permitido es 20", status_code=422)

    def test_espacios_se_analizan_no_se_recortan(self):
        r = self.client.post(reverse("representacion:texto"), {"texto": "a b"})
        self.assertEqual(len(r.context["caracteres"]), 3)

    def test_salud(self):
        r = self.client.get(reverse("representacion:salud"))
        self.assertJSONEqual(r.content, {"estado": "ok"})

    def test_metodo_no_permitido(self):
        self.assertEqual(self.client.delete(reverse("representacion:numero")).status_code, 405)
