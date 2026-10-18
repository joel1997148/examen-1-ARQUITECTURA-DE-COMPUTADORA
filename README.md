# Analizador de representación de datos

Este proyecto es una aplicación web hecha con **Python 3.12** y **Django 5.2**. La idea es juntar tres temas que vimos en la materia: los sistemas numéricos, la codificación de caracteres y la ejecución de programas en contenedores.

La aplicación tiene dos partes:

1. **Conversión de números:** escribes un número, eliges la base en la que está (2, 8, 10 o 16) y el programa lo muestra en decimal, binario, octal y hexadecimal. El binario se completa con ceros hasta llegar a un byte completo (8, 16 bits…). También dice cuántos bits significativos tiene el número y cuántos bytes necesita.
2. **Análisis de caracteres:** escribes un texto de hasta 20 caracteres y, por cada letra, muestra su código decimal, su punto de código Unicode (U+…), su valor en hexadecimal y los bytes que ocupa en UTF-8.

Si el número está vacío, tiene dígitos que no corresponden a la base, es negativo o se pasa de 65 535, el programa muestra un mensaje explicando el error.

## Cómo está organizado el proyecto

```
config/              configuración general de Django (settings, urls, wsgi)
representacion/      la app principal
  services.py        aquí están los cálculos: conversiones, bits, bytes y UTF-8
  forms.py           los dos formularios y sus validaciones
  views.py           las vistas que reciben los datos y muestran la página
  urls.py            las rutas de la app
  templates/         el HTML de la página
  tests/             las pruebas automatizadas
evidencias/          capturas de docker stats
Dockerfile
compose.yaml
requirements.txt
manage.py
```

Decidí poner los cálculos en `services.py`, separados de las vistas. Así las vistas solo reciben el formulario, llaman a la función que corresponde y muestran el resultado. Esto me sirvió mucho para hacer las pruebas, porque puedo probar las conversiones sin tener que levantar el servidor.

La aplicación no usa base de datos porque no guarda nada, solo hace cálculos. Por eso no hay modelos.

## Cómo ejecutarlo

### En la computadora (PowerShell)

Abrir la carpeta del proyecto en Visual Studio Code, abrir una terminal y ejecutar:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py test -v 2
python manage.py runserver
```

- El primer comando crea el entorno virtual.
- El segundo lo activa (en la terminal debe aparecer `(.venv)` al inicio).
- El tercero instala Django y gunicorn.
- El cuarto corre las pruebas.
- El último inicia el servidor.

Después hay que abrir http://127.0.0.1:8000 en el navegador. Para detener el servidor se presiona `Ctrl + C`.

Si al activar el entorno aparece un error de "ejecución de scripts deshabilitada", hay que ejecutar esto una vez:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

### Con Docker

Primero hay que tener Docker Desktop abierto. Luego, en la misma carpeta:

```powershell
docker compose up -d --build
docker compose ps
```

La aplicación queda en http://localhost:8000. El contenedor está limitado a **256 MB de RAM y 1 CPU**; eso está configurado en `compose.yaml`:

```yaml
deploy:
  resources:
    limits:
      cpus: "1.0"
      memory: 256M
```

Para correr las pruebas dentro del contenedor:

```powershell
docker compose run --rm -e DJANGO_DEBUG=1 web python manage.py test -v 2
```

Para ver el consumo de recursos:

```powershell
docker stats analizador-datos
```

Para apagar todo:

```powershell
docker compose down
```

Dentro del contenedor no uso `runserver`, sino **gunicorn**, porque `runserver` es solo para desarrollo. También configuré el contenedor para que no corra como administrador (root) y para que su sistema de archivos sea de solo lectura.

## Evidencia de docker stats

Con el contenedor corriendo, `docker stats` mostró lo siguiente en mi computadora:

| CPU % | Uso de memoria / límite | MEM % |
|---|---|---|
| __ % | __ MiB / 256 MiB | __ % |

La captura de pantalla está en `evidencias/docker_stats.png`. En la columna de memoria se ve que el límite es de 256 MiB.

## Pruebas

Hice 24 pruebas que se dividen en dos archivos:

- `test_services.py` prueba los cálculos directamente:
  - conversiones desde cada base, incluyendo los límites 0 y 65 535;
  - errores de dígitos (por ejemplo `102` en base 2);
  - valores negativos y fuera de rango;
  - el caso de la **ñ**, que debe dar U+00F1 y los bytes `C3 B1`.
- `test_views.py` prueba la aplicación como si fuera un navegador: que la página cargue, que una conversión válida muestre el resultado, que un error muestre el mensaje y que el texto con ñ se analice bien.

Algo que encontré al probar es que la función `int()` de Python acepta cosas como `0x1F`, `0b101`, `1_000` o `+5`, aunque esos no son dígitos válidos de la base. Por eso la validación revisa cada carácter contra los dígitos permitidos y no depende solo de `int()`.

## Arquitectura de Von Neumann

La aplicación usa los componentes de la arquitectura de Von Neumann así:

- **CPU:** ejecuta las instrucciones del programa con el ciclo de buscar, decodificar y ejecutar. Las conversiones son operaciones que hace la ALU, como las divisiones para cambiar de base o el cálculo `(bits + 7) // 8` para redondear a bytes.
- **Memoria:** el programa (el código de Python y Django) y los datos (el número, el texto y los resultados) están en la misma memoria RAM. Esa es la idea principal de Von Neumann: programa y datos juntos. En el contenedor esa memoria está limitada a 256 MB.
- **Entrada y salida:** el formulario es la entrada; los datos llegan por la red como una petición HTTP. La página con los resultados es la salida.
- **Buses:** conectan la CPU con la memoria y con los dispositivos de entrada y salida.

La aplicación también muestra que todo en la computadora se guarda en bits: el número aparece en binario agrupado en bytes y cada letra aparece con sus bytes en UTF-8.

## Por qué el contenedor comparte el kernel del host

Un contenedor no es una máquina virtual. No tiene su propio sistema operativo completo: es un proceso que corre sobre el kernel del sistema anfitrión, pero aislado. Ese aislamiento lo hace el propio kernel de Linux con dos herramientas:

- **Namespaces:** hacen que el contenedor vea sus propios procesos, su propia red y sus propios archivos, como si estuviera solo.
- **cgroups:** limitan cuántos recursos puede usar. Los límites de 256 MB y 1 CPU funcionan gracias a los cgroups, y `docker stats` lee esos valores.

La imagen `python:3.12-slim` solo trae las librerías, Python y la aplicación; el kernel lo pone el host. Por eso el contenedor arranca en pocos segundos y ocupa mucho menos que una máquina virtual.

En mi caso uso Windows, que no tiene kernel Linux. Docker Desktop usa **WSL 2**, que ejecuta un kernel Linux liviano, y el contenedor comparte ese kernel. En un servidor con Linux compartiría directamente el kernel del servidor.

## Entrega

- Repositorio: https://github.com/joel1997148/examen-1-ARQUITECTURA-DE-COMPUTADORA
- Video: https://youtu.be/t3AgY01hG3o
