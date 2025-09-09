# parse_comprobante_full.py
# Requiere: pdfplumber, pandas, openpyxl

import io
from fastapi import UploadFile
import pandas as pd
import pdfplumber

import pdfplumber

# ----------- VALIDACIÓN DE PLANTILLA 1 -----------
def check_plantilla1(file: UploadFile) -> bool:
    file.file.seek(0)  # rebobinar
    with pdfplumber.open(file.file) as pdf:
        text = (pdf.pages[0].extract_text() or "").lower()
        keywords = [
            "documento no valido como factura",
            "farmacias red resistencia",
            "listado de vencimientos",
        ]
        return all(kw in text for kw in keywords)

# -------------   PASAR PDF A EXCEL   -------------
def extract_clean_lines(file: UploadFile) -> list[str]:
    """
    Extrae y limpia las líneas relevantes de un PDF.
    Devuelve solo las líneas comprendidas entre la cabecera y el pie de página.
    """
    file.file.seek(0)
    lines_clean = []

    with pdfplumber.open(file.file) as pdf:
        for page in pdf.pages:
            lines = (page.extract_text() or "").splitlines()
            keep = False
            for line in map(str.strip, lines):
                if not line:
                    continue
                if line.lower().startswith("lote vencimiento"):
                    keep = True
                    continue
                if line.startswith("(*) Productos Trazables") or line.lower().startswith("página "):
                    keep = False
                elif keep:
                    lines_clean.append(line)
    return lines_clean


def parse_products(lines_clean: list[str]) -> list[dict]:
    """
    Parsea bloques de productos a partir de las líneas limpias.
    Cada producto puede incluir varios lotes y un total.
    """
    data = []
    i = 0

    while i < len(lines_clean):
        product_name = lines_clean[i]   # nombre del producto
        i += 1

        while i < len(lines_clean) and not lines_clean[i].startswith('Totales'):
            lote_line = lines_clean[i]
            i += 1

            # línea opcional de Totales
            total_line = ""
            if i < len(lines_clean) and lines_clean[i].startswith('Totales'):
                total_line = lines_clean[i]
                i += 1

            total_num = total_line.replace('Totales', '').strip() if total_line else ""

            # dividir la línea de lote
            parts = lote_line.split()
            if len(parts) < 3:
                continue  # línea inválida, se ignora

            lote = parts[0]
            venc = parts[1]
            cantidad = parts[-1]
            proveedor = " ".join(parts[2:-1]) if len(parts) > 3 else ""

            data.append({
                "Producto": product_name,
                "Lote": lote,
                "Vencimiento": venc,
                "Proveedor": proveedor,
                "Cantidad": cantidad,
                "Totales": total_num
            })

            if total_line:
                break

    return data


def convert_pdf_2_excel(file: UploadFile) -> io.BytesIO:
    """
    Convierte un PDF de la plantilla en un archivo Excel en memoria.
    """
    lines_clean = extract_clean_lines(file)
    data = parse_products(lines_clean)

    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    output.seek(0)
    return output