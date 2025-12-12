import os
import sys
import subprocess
import tempfile
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter.font import Font

from PyPDF2 import PdfReader, PdfWriter, PdfMerger
from fpdf import FPDF
from PIL import Image

import mammoth  # para convertir DOCX a HTML
import re


# ================================================================
#  RESOURCE PATH (FUNCIONA PARA PYINSTALLER ONEFILE)
# ================================================================
def resource_path(relative_path):
    """Obtiene ruta absoluta tanto en desarrollo como dentro del EXE."""
    if getattr(sys, 'frozen', False):  # PyInstaller
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


# ================================================================
#  FUNCIONES DE PROCESAMIENTO
# ================================================================
def clean_pdf(input_path, output_path):
    """Limpia y reescribe un PDF para evitar errores en la fusión."""
    try:
        reader = PdfReader(input_path)
        writer = PdfWriter()

        for page in reader.pages:
            writer.add_page(page)

        with open(output_path, "wb") as f:
            writer.write(f)
        return True

    except Exception as e:
        print(f"[ERROR] Limpieza de PDF: {e}")
        return False


def txt_to_pdf(txt_path, output_pdf):
    """Convierte archivo TXT a PDF."""
    try:
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        with open(txt_path, "r", encoding="utf-8") as f:
            for line in f:
                pdf.multi_cell(0, 8, line.strip())

        pdf.output(output_pdf)
    except Exception as e:
        print(f"[ERROR] TXT → PDF: {e}")


def image_to_pdf(image_path, output_pdf):
    """Convierte JPG/PNG a PDF."""
    try:
        image = Image.open(image_path)
        image = image.convert("RGB")
        image.save(output_pdf, "PDF", resolution=150.0)
    except Exception as e:
        print(f"[ERROR] Imagen → PDF: {e}")


# ================================================================
#   DOCX → PDF SIN MICROSOFT WORD
# ================================================================
def docx_to_pdf(docx_path, output_pdf):
    """
    Convierte DOCX a PDF sin Word.
    Usa LibreOffice portable si está disponible; si no, Mammoth (DOCX→HTML→PDF).
    """

    # 1) Intentar LibreOffice Portable (portable en /assets/lo/)
    soffice = resource_path("assets/lo/soffice.exe")
    if os.path.exists(soffice):
        try:
            subprocess.run([
                soffice,
                "--headless",
                "--convert-to", "pdf",
                "--outdir", str(Path(output_pdf).parent),
                docx_path
            ], check=True)
            return
        except Exception as e:
            print(f"[WARN] LibreOffice conversion falló: {e}")

    # 2) Fallback con Mammoth (DOCX → HTML → PDF)
    try:
        with open(docx_path, "rb") as f:
            result = mammoth.convert_to_html(f)
            html = result.value

        # convertir HTML a PDF con FPDF "manual"
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        clean_text = re.sub("<[^<]+?>", "", html)

        pdf.multi_cell(0, 8, clean_text)
        pdf.output(output_pdf)

    except Exception as e:
        print(f"[ERROR] DOCX → PDF (fallback): {e}")


# ================================================================
#    GHOSTSCRIPT PORTABLE (PDF COMPRESSOR)
# ================================================================
def get_gs_path():
    """Devuelve ruta a Ghostscript portable dentro del EXE."""
    candidate = resource_path("assets/gs/bin/gswin64c.exe")
    if os.path.exists(candidate):
        return candidate

    # fallback: sistema
    return "gs"


def compress_pdf(input_pdf, output_pdf, quality="medium"):
    gs = get_gs_path()

    quality_settings = {
        "low": "/screen",
        "medium": "/ebook",
        "high": "/prepress"
    }

    setting = quality_settings.get(quality, "/ebook")

    cmd = [
        gs,
        "-sDEVICE=pdfwrite",
        f"-dPDFSETTINGS={setting}",
        "-dNOPAUSE",
        "-dQUIET",
        "-dBATCH",
        f"-sOutputFile={output_pdf}",
        input_pdf
    ]

    try:
        subprocess.run(cmd, check=True)
        return True
    except Exception as e:
        print(f"[ERROR] Ghostscript: {e}")
        return False


# ================================================================
#   REGISTRO DE PROCESADORES POR EXTENSIÓN
# ================================================================
PROCESSORS = {}


def register(exts):
    """Decorador para registrar funciones de procesamiento."""
    def wrapper(func):
        for e in exts:
            PROCESSORS[e.lower()] = func
        return func
    return wrapper


@register([".pdf"])
def proc_pdf(path, temp_dir, merger):
    temp_pdf = os.path.join(temp_dir, f"{Path(path).stem}_clean.pdf")
    if clean_pdf(path, temp_pdf):
        merger.append(temp_pdf)


@register([".txt"])
def proc_txt(path, temp_dir, merger):
    temp_pdf = os.path.join(temp_dir, f"{Path(path).stem}.pdf")
    txt_to_pdf(path, temp_pdf)
    merger.append(temp_pdf)


@register([".jpg", ".jpeg", ".png"])
def proc_img(path, temp_dir, merger):
    temp_pdf = os.path.join(temp_dir, f"{Path(path).stem}.pdf")
    image_to_pdf(path, temp_pdf)
    merger.append(temp_pdf)


@register([".docx"])
def proc_docx(path, temp_dir, merger):
    temp_pdf = os.path.join(temp_dir, f"{Path(path).stem}.pdf")
    docx_to_pdf(path, temp_pdf)
    merger.append(temp_pdf)


# ================================================================
#   FUNCIÓN PRINCIPAL DE COMPILACIÓN
# ================================================================
def compile_files(paths):
    if not paths:
        raise ValueError("No hay archivos para procesar")

    temp_dir = tempfile.mkdtemp(prefix="compiler_")
    merger = PdfMerger()

    for path in paths:
        ext = Path(path).suffix.lower()
        handler = PROCESSORS.get(ext)

        if handler:
            try:
                handler(path, temp_dir, merger)
            except Exception as e:
                print(f"[ERROR] procesando {path}: {e}")
        else:
            print(f"[WARN] Extensión no soportada: {ext}")

    if len(merger.pages) == 0:
        raise ValueError("No se generó ningún PDF válido")

    final_pdf = os.path.join(temp_dir, "output.pdf")
    merger.write(final_pdf)
    merger.close()

    return final_pdf, temp_dir


# ================================================================
#  INTERFAZ GRÁFICA (TK)
# ================================================================
def select_files():
    files = filedialog.askopenfilenames(
        title="Seleccionar archivos",
        filetypes=[("Documentos", "*.pdf *.docx *.txt *.jpg *.jpeg *.png")]
    )
    if files:
        file_list.delete(0, tk.END)
        for f in files:
            file_list.insert(tk.END, f)


def run_process():
    try:
        paths = list(file_list.get(0, tk.END))
        if not paths:
            messagebox.showwarning("Aviso", "Seleccione archivos primero.")
            return

        output_pdf, temp_dir = compile_files(paths)

        # compresión opcional
        quality = quality_var.get()
        compressed_pdf = os.path.join(temp_dir, "output_compressed.pdf")

        compress_pdf(output_pdf, compressed_pdf, quality)

        # guardar
        save_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            initialfile="resultado.pdf",
            filetypes=[("PDF", "*.pdf")]
        )

        if save_path:
            os.replace(compressed_pdf, save_path)
            messagebox.showinfo("Listo", "PDF generado correctamente.")

    except Exception as e:
        messagebox.showerror("Error", str(e))


# ================================================================
#   VENTANA PRINCIPAL TKINTER
# ================================================================
root = tk.Tk()
root.title("Compilador PDF Portable")

root.geometry("500x550")
root.resizable(False, False)

title_font = Font(family="Helvetica", size=16, weight="bold")
title_label = tk.Label(root, text="Compilador PDF", font=title_font)
title_label.pack(pady=10)

file_list = tk.Listbox(root, width=60, height=12)
file_list.pack(pady=10)

ttk.Button(root, text="Seleccionar archivos", command=select_files).pack(pady=5)

# calidad
quality_var = tk.StringVar(value="medium")

ttk.Label(root, text="Calidad de compresión:").pack()
ttk.Combobox(
    root,
    textvariable=quality_var,
    values=["low", "medium", "high"],
    state="readonly",
    width=15
).pack(pady=5)

ttk.Button(root, text="Generar PDF", command=run_process).pack(pady=20)

root.mainloop()
