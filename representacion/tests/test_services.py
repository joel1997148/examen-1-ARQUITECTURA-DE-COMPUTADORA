"""Pruebas unitarias de la lógica pura (sin Django)."""

from unittest import TestCase

from representacion import services as s


class ConversionesValidasTests(TestCase):
    def test_conversiones_desde_cada_base(self):
        casos = [
            # (texto, base, decimal, binario ajustado, octal, hex, bits, bytes)
            ("0", 10, 0, "00000000", "0", "0", 1, 1),
            ("255", 10, 255, "11111111", "377", "FF", 8, 1),
            ("256", 10, 256, "0000000100000000", "400", "100", 9, 2),
            ("1F4", 16, 500, "0000000111110100", "764", "1F4", 9, 2),
            ("1f4", 16, 500, "0000000111110100", "764", "1F4", 9, 2),
            ("777", 8, 511, "0000000111111111", "777", "1FF", 9, 2),
            ("1010", 2, 10, "00001010", "12", "A", 4, 1),
            ("FFFF", 16, 65535, "1111111111111111", "177777", "FFFF", 16, 2),
            ("  42  ", 10, 42, "00101010", "52", "2A", 6, 1),
        ]
        for texto, base, dec, binario, octal, hexa, bits, nbytes in casos:
            with self.subTest(texto=texto, base=base):
                r = s.convertir(s.parsear_numero(texto, base))
                self.assertEqual(r.decimal, dec)
                self.assertEqual(r.binario, binario)
                self.assertEqual(r.octal, octal)
                self.assertEqual(r.hexadecimal, hexa)
                self.assertEqual(r.bits_significativos, bits)
                self.assertEqual(r.bytes_necesarios, nbytes)
                self.assertEqual(len(r.binario) % 8, 0)

    def test_binario_agrupado_por_bytes(self):
        self.assertEqual(s.convertir(500).binario_agrupado, "00000001 11110100")
        self.assertEqual(s.convertir(500).bits_ajustados, 16)

    def test_limites_del_rango(self):
        self.assertEqual(s.parsear_numero("0", 10), 0)
        self.assertEqual(s.parsear_numero("65535", 10), 65535)
        self.assertEqual(s.parsear_numero("1111111111111111", 2), 65535)


class ErroresDeValidacionTests(TestCase):
    def assertError(self, texto, base, fragmento):
        with self.assertRaises(s.ErrorDeValidacion) as ctx:
            s.parsear_numero(texto, base)
        self.assertIn(fragmento, str(ctx.exception))

    def test_entrada_vacia_o_espacios(self):
        for texto in ("", "   ", None):
            with self.subTest(texto=texto):
                self.assertError(texto, 10, "no puede estar vacío")

    def test_digitos_invalidos_para_la_base(self):
        self.assertError("102", 2, "'2'")
        self.assertError("89", 8, "'8', '9'")
        self.assertError("12A", 10, "'A'")
        self.assertError("FG", 16, "'G'")

    def test_rechaza_lo_que_int_aceptaria(self):
        # int() acepta prefijos, guiones bajos y '+': aquí no son dígitos válidos
        for texto, base in (("0x1F", 16), ("0b101", 2), ("1_000", 10), ("+5", 10), ("1 0", 10)):
            with self.subTest(texto=texto):
                with self.assertRaises(s.ErrorDeValidacion):
                    s.parsear_numero(texto, base)

    def test_negativos(self):
        self.assertError("-5", 10, "negativos")
        self.assertError("-1", 16, "negativos")

    def test_fuera_de_rango(self):
        self.assertError("65536", 10, "fuera del rango")
        self.assertError("10000", 16, "fuera del rango")
        self.assertError("1" * 17, 2, "fuera del rango")

    def test_base_no_permitida(self):
        self.assertError("10", 3, "base seleccionada no es válida")


class Utf8Tests(TestCase):
    def test_enie_ocupa_dos_bytes(self):
        (c,) = s.analizar_texto("ñ")
        self.assertEqual(c.decimal, 241)
        self.assertEqual(c.punto_codigo, "U+00F1")
        self.assertEqual(c.hexadecimal, "F1")
        self.assertEqual(c.bytes_utf8, "C3 B1")
        self.assertEqual(c.cantidad_bytes, 2)

    def test_uno_a_cuatro_bytes(self):
        casos = {"A": ("U+0041", "41", 1), "é": ("U+00E9", "C3 A9", 2),
                 "€": ("U+20AC", "E2 82 AC", 3), "😀": ("U+1F600", "F0 9F 98 80", 4)}
        for car, (cp, utf8, n) in casos.items():
            with self.subTest(car=car):
                (c,) = s.analizar_texto(car)
                self.assertEqual((c.punto_codigo, c.bytes_utf8, c.cantidad_bytes), (cp, utf8, n))

    def test_texto_con_enie_en_contexto(self):
        r = s.analizar_texto("Año")
        self.assertEqual([c.caracter for c in r], ["A", "ñ", "o"])
        self.assertEqual(sum(c.cantidad_bytes for c in r), 4)

    def test_limite_de_20_caracteres(self):
        self.assertEqual(len(s.analizar_texto("x" * 20)), 20)
        with self.assertRaises(s.ErrorDeValidacion) as ctx:
            s.analizar_texto("x" * 21)
        self.assertIn("máximo permitido es 20", str(ctx.exception))

    def test_texto_vacio(self):
        with self.assertRaises(s.ErrorDeValidacion):
            s.analizar_texto("")
