"""Lógica de dominio: sistemas numéricos y codificación de caracteres.

Este módulo no depende de Django. Las vistas y formularios lo usan, y las
pruebas lo verifican de forma aislada.
"""

from __future__ import annotations

from dataclasses import dataclass

BASES_PERMITIDAS: dict[int, str] = {
    2: "01",
    8: "01234567",
    10: "0123456789",
    16: "0123456789ABCDEF",
}
NOMBRE_BASE = {2: "binaria", 8: "octal", 10: "decimal", 16: "hexadecimal"}
VALOR_MINIMO = 0
VALOR_MAXIMO = 65_535
MAX_CARACTERES = 20


class ErrorDeValidacion(ValueError):
    """Error de entrada con un mensaje listo para mostrar al usuario."""


@dataclass(frozen=True)
class ResultadoConversion:
    decimal: int
    binario: str          # completado al siguiente múltiplo de 8 bits
    octal: str
    hexadecimal: str
    bits_significativos: int
    bytes_necesarios: int

    @property
    def bits_ajustados(self) -> int:
        return self.bytes_necesarios * 8

    @property
    def binario_agrupado(self) -> str:
        """Binario separado por bytes para lectura: '00000001 11110100'."""
        return " ".join(self.binario[i:i + 8] for i in range(0, len(self.binario), 8))


@dataclass(frozen=True)
class AnalisisCaracter:
    caracter: str
    decimal: int
    punto_codigo: str     # U+00F1
    hexadecimal: str      # F1
    bytes_utf8: str       # C3 B1
    cantidad_bytes: int


def _formatear_numero_es(n: int) -> str:
    return f"{n:,}".replace(",", " ")


def parsear_numero(texto: str | None, base: int) -> int:
    """Valida ``texto`` como número en ``base`` y devuelve su valor entero.

    A diferencia de ``int(texto, base)``, rechaza prefijos (0x, 0b), guiones
    bajos, signos y espacios internos, para que solo se acepten dígitos reales
    de la base elegida.
    """
    if base not in BASES_PERMITIDAS:
        raise ErrorDeValidacion("La base seleccionada no es válida. Elija 2, 8, 10 o 16.")

    limpio = (texto or "").strip()
    if not limpio:
        raise ErrorDeValidacion("Ingrese un número; el campo no puede estar vacío.")
    if limpio.startswith("-"):
        raise ErrorDeValidacion(
            "No se admiten valores negativos. Ingrese un número entre 0 y 65 535."
        )

    validos = BASES_PERMITIDAS[base]
    invalidos = sorted({c for c in limpio.upper() if c not in validos})
    if invalidos:
        lista = ", ".join(f"'{c}'" for c in invalidos)
        rango = f"0-{validos[-1]}" if base <= 10 else "0-9 y A-F"
        raise ErrorDeValidacion(
            f"Dígitos inválidos para la base {base} ({NOMBRE_BASE[base]}): {lista}. "
            f"Solo se permiten {rango}."
        )

    valor = int(limpio, base)
    if not VALOR_MINIMO <= valor <= VALOR_MAXIMO:
        raise ErrorDeValidacion(
            f"El valor {_formatear_numero_es(valor)} está fuera del rango permitido "
            f"(0 a 65 535, es decir, 16 bits sin signo)."
        )
    return valor


def convertir(valor: int) -> ResultadoConversion:
    """Representa ``valor`` en las cuatro bases y calcula bits y bytes."""
    if not VALOR_MINIMO <= valor <= VALOR_MAXIMO:
        raise ErrorDeValidacion("El valor está fuera del rango permitido (0 a 65 535).")
    bits = max(1, valor.bit_length())   # el 0 necesita 1 bit para representarse
    bytes_necesarios = (bits + 7) // 8  # techo sin usar float
    return ResultadoConversion(
        decimal=valor,
        binario=format(valor, f"0{bytes_necesarios * 8}b"),
        octal=format(valor, "o"),
        hexadecimal=format(valor, "X"),
        bits_significativos=bits,
        bytes_necesarios=bytes_necesarios,
    )


def analizar_caracter(c: str) -> AnalisisCaracter:
    codigo = ord(c)
    datos = c.encode("utf-8")
    return AnalisisCaracter(
        caracter=c,
        decimal=codigo,
        punto_codigo=f"U+{codigo:04X}",
        hexadecimal=f"{codigo:X}",
        bytes_utf8=datos.hex(" ").upper(),
        cantidad_bytes=len(datos),
    )


def analizar_texto(texto: str | None) -> list[AnalisisCaracter]:
    """Analiza cada carácter (punto de código) de un texto de hasta 20."""
    if texto is None or texto == "":
        raise ErrorDeValidacion("Ingrese un texto; el campo no puede estar vacío.")
    if len(texto) > MAX_CARACTERES:
        raise ErrorDeValidacion(
            f"El texto tiene {len(texto)} caracteres; el máximo permitido es {MAX_CARACTERES}."
        )
    return [analizar_caracter(c) for c in texto]
