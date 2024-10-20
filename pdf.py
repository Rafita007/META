import PyPDF2
import re
import pandas as pd


def extraer_texto_pdf(ruta_pdf):
    with open(ruta_pdf, 'rb') as archivo_pdf:
        lector = PyPDF2.PdfReader(archivo_pdf)

        texto_completo = ''
        for pagina in lector.pages:
            texto_completo += pagina.extract_text() + '\n'

    return texto_completo


def detectar_fechas(texto):
    patron_fecha = r'(\d{2}/\d{2}/\d{4})(?=\D|$)'  # Busca fechas en el formato dd/mm/yyyy
    fechas = re.findall(patron_fecha, texto)
    return fechas


def detectar_descripciones(texto):
    lineas = texto.splitlines()
    descripciones = []
    inicio_descripciones = False

    for linea in lineas:
        if re.search(r'\d{2}/\d{2}/\d{4}Descripción', linea):
            inicio_descripciones = True
            continue

        if inicio_descripciones:
            if "Cargos Abonos" in linea:
                descripcion = linea.split("Cargos Abonos")[0].strip()
                if descripcion:
                    descripciones.append(descripcion)
                inicio_descripciones = False
                continue

            if linea.strip():
                descripciones.append(linea.strip())

    return descripciones


def extraer_datos_financieros(texto):
    patron_cantidad = r'\$\d+\,?\d*\.\d{2}'
    lineas = texto.splitlines()
    inicio_datos = False
    cargos = []
    abonos = []
    saldos = []
    estado = 'cargos'

    for linea in lineas:
        if 'Cargos Abonos Saldo' in linea or 'Cargos Abonos' in linea:
            inicio_datos = True
            estado = 'cargos'
            continue

        if inicio_datos:
            cantidades = re.findall(patron_cantidad, linea)

            if cantidades:
                if estado == 'cargos':
                    if len(cantidades) == 1:
                        cargos.append(cantidades[0])
                    elif len(cantidades) == 2:
                        cargos.append(cantidades[0])
                        abonos.append(cantidades[1])
                        estado = 'abonos'
                elif estado == 'abonos':
                    if len(cantidades) == 1:
                        abonos.append(cantidades[0])
                    elif len(cantidades) == 2:
                        abonos.append(cantidades[0])
                        saldos.append(cantidades[1])
                        estado = 'saldos'
                elif estado == 'saldos':
                    if len(cantidades) == 1:
                        saldos.append(cantidades[0])
            else:
                inicio_datos = False

    return cargos, abonos, saldos
