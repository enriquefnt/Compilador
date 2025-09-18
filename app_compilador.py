import sys
import os
import subprocess
import time
import shutil
import tempfile  # Para crear carpeta temporal estándar
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image
from docx import Document
from fpdf import FPDF
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from PyPDF2.errors import PdfReadError
from pathlib import Path  # Para manejo seguro de rutas

# Variables globales para modo y archivos seleccionados
selected_mode = None
selected_files = []


def txt_to_pdf(text_path, pdf_path):
    """Convierte un archivo de texto a PDF."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)
    with open(text_path, "r", encoding="utf-8") as f:
        for line in f:
            pdf.multi_cell(0, 10, line)
    pdf.output(pdf_path)


def docx_to_pdf(docx_path, pdf_path):
    """Convierte un archivo DOCX a PDF."""
    doc = Document(docx_path)
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)
    for para in doc.paragraphs:
        pdf.multi_cell(0, 10, para.text)
    pdf.output(pdf_path)


def image_to_pdf(image_path, pdf_path):
    """Convierte una imagen a PDF."""
    image = Image.open(image_path)
    if image.mode == "RGBA":
        image = image.convert("RGB")
    image.save(pdf_path, "PDF", resolution=100.0)


def clean_pdf(input_path, output_path):
    """
    Limpia un PDF para evitar errores de lectura.
    Devuelve True si se pudo limpiar, False si el PDF está corrupto.
    """
    try:
        reader = PdfReader(input_path)
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        writer.add_metadata({})
        with open(output_path, "wb") as f_out:
            writer.write(f_out)
        return True
    except PdfReadError as e:
        print(f"Error leyendo el PDF {input_path}: {e}. Saltando este archivo.")
        return False


def compress_pdf(input_path, output_path, compression_level="none"):
    """
    Comprime el PDF usando Ghostscript según el nivel de compresión.
    """
    if compression_level == "none":
        return input_path

    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    gs_executable = os.path.join(base_path,"DistribucionApp", "gs", "gs10.05.1", "bin", "gswin64c.exe")
    # gs_executable = os.path.join(base_path, "gs", "gs10.05.1", "bin", "gswin64c.exe")

    print("Ruta a Ghostscript:", gs_executable)
    print("¿Existe Ghostscript en esa ruta?", os.path.exists(gs_executable))

    if compression_level == "ebook":
        pdf_setting = "/ebook"
    elif compression_level == "screen":
        pdf_setting = "/screen"
    else:
        pdf_setting = "/screen"

    args = [
        gs_executable,
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.4",
        f"-dPDFSETTINGS={pdf_setting}",
        "-dNOPAUSE",
        "-dQUIET",
        "-dBATCH",
        f"-sOutputFile={output_path}",
        input_path
    ]
    try:
        subprocess.run(args, check=True)
        if os.path.exists(output_path):
            print(f"Archivo comprimido creado: {output_path}, tamaño: {os.path.getsize(output_path)} bytes")
        else:
            print(f"Archivo comprimido NO creado: {output_path}")
        try:
            if os.path.exists(output_path) and os.path.getsize(output_path) < os.path.getsize(input_path):
                return output_path
            else:
                if os.path.exists(output_path):
                    os.remove(output_path)
                return input_path
        except Exception as e:
            print(f"Error verificando tamaño archivo comprimido: {e}")
            return input_path
    except Exception as e:
        print(f"Error al comprimir PDF: {e}")
        return input_path


def compile_pdfs_in_directory(directory):
    """
    Compila y une PDFs a partir de todos los archivos en un directorio.
    Usa una carpeta temporal estándar para archivos intermedios.
    """
    temp_dir = tempfile.mkdtemp(prefix="temp_pdfs_compilador_")
    print(f"Carpeta temporal creada para directorio: {temp_dir}")

    merger = PdfMerger()

    for filename in sorted(os.listdir(directory)):
        filepath = os.path.join(directory, filename)
        name, ext = os.path.splitext(filename)
        ext = ext.lower()

        try:
            if ext == ".pdf":
                temp_pdf = os.path.join(temp_dir, f"{name}_clean.pdf")
                print(f"Limpiando PDF: {filepath} -> {temp_pdf}")
                if clean_pdf(filepath, temp_pdf):
                    merger.append(temp_pdf)
                else:
                    print(f"Saltando PDF corrupto: {filepath}")
            elif ext in [".png", ".jpg", ".jpeg"]:
                temp_pdf = os.path.join(temp_dir, f"{name}_temp.pdf")
                print(f"Convirtiendo imagen a PDF: {filepath} -> {temp_pdf}")
                image_to_pdf(filepath, temp_pdf)
                merger.append(temp_pdf)
            elif ext == ".txt":
                temp_pdf = os.path.join(temp_dir, f"{name}_temp.pdf")
                print(f"Convirtiendo txt a PDF: {filepath} -> {temp_pdf}")
                txt_to_pdf(filepath, temp_pdf)
                merger.append(temp_pdf)
            elif ext == ".docx":
                temp_pdf = os.path.join(temp_dir, f"{name}_temp.pdf")
                print(f"Convirtiendo docx a PDF: {filepath} -> {temp_pdf}")
                docx_to_pdf(filepath, temp_pdf)
                merger.append(temp_pdf)
            else:
                print(f"Extensión no soportada: {ext}, archivo: {filepath}")
        except Exception as e:
            print(f"Error procesando {filepath}: {e}. Saltando este archivo.")

    dir_name = os.path.basename(os.path.normpath(directory))
    output_pdf = os.path.join(directory, f"{dir_name}_UNIDO.pdf")
    print(f"Archivo PDF final: {output_pdf}")

    if len(merger.pages) > 0:
        merger.write(output_pdf)
        merger.close()
    else:
        merger.close()
        shutil.rmtree(temp_dir)
        raise ValueError("No se encontraron archivos PDF válidos para compilar.")

    size_bytes = os.path.getsize(output_pdf)
    print(f"Tamaño archivo final: {size_bytes} bytes")

    if size_bytes < 3 * 1024 * 1024:
        compression_level = "none"
    elif size_bytes < 8 * 1024 * 1024:
        compression_level = "ebook"
    else:
        compression_level = "screen"

    compressed_pdf = os.path.join(directory, f"{dir_name}_unido_comprimido.pdf")
    print(f"Archivo PDF comprimido: {compressed_pdf}")
    final_pdf = compress_pdf(output_pdf, compressed_pdf, compression_level=compression_level)

    # Si se creó un archivo comprimido, reemplazamos el original y devolvemos la ruta correcta
    if final_pdf != output_pdf:
        os.replace(final_pdf, output_pdf)
        final_path = output_pdf
    else:
        final_path = output_pdf

    try:
        shutil.rmtree(temp_dir)
    except Exception as e:
        print(f"Error eliminando directorio temporal {temp_dir}: {e}")

    # Devolvemos la ruta del archivo final (comprimido o no)
    return final_path


def compile_pdfs_from_files(files):
    """
    Compila y une PDFs a partir de una lista de archivos específicos.
    Usa una carpeta temporal estándar para archivos intermedios.
    NOTA: No elimina la carpeta temporal aquí para evitar borrar el archivo final antes de moverlo.
    """
    temp_dir = tempfile.mkdtemp(prefix="temp_pdfs_compilador_")
    print(f"Carpeta temporal creada para archivos: {temp_dir}")

    merger = PdfMerger()

    for filepath in files:
        print(f"Procesando archivo: {filepath}")
        name, ext = os.path.splitext(os.path.basename(filepath))
        ext = ext.lower()

        try:
            if ext == ".pdf":
                temp_pdf = os.path.join(temp_dir, f"{name}_clean.pdf")
                print(f"Limpiando PDF: {filepath} -> {temp_pdf}")
                if clean_pdf(filepath, temp_pdf):
                    merger.append(temp_pdf)
                else:
                    print(f"Saltando PDF corrupto: {filepath}")
            elif ext in [".png", ".jpg", ".jpeg"]:
                temp_pdf = os.path.join(temp_dir, f"{name}_temp.pdf")
                print(f"Convirtiendo imagen a PDF: {filepath} -> {temp_pdf}")
                image_to_pdf(filepath, temp_pdf)
                merger.append(temp_pdf)
            elif ext == ".txt":
                temp_pdf = os.path.join(temp_dir, f"{name}_temp.pdf")
                print(f"Convirtiendo txt a PDF: {filepath} -> {temp_pdf}")
                txt_to_pdf(filepath, temp_pdf)
                merger.append(temp_pdf)
            elif ext == ".docx":
                temp_pdf = os.path.join(temp_dir, f"{name}_temp.pdf")
                print(f"Convirtiendo docx a PDF: {filepath} -> {temp_pdf}")
                docx_to_pdf(filepath, temp_pdf)
                merger.append(temp_pdf)
            else:
                print(f"Extensión no soportada: {ext}, archivo: {filepath}")
        except Exception as e:
            print(f"Error procesando {filepath}: {e}. Saltando este archivo.")

    output_pdf = os.path.join(temp_dir, "temp_output.pdf")
    print(f"Archivo PDF final temporal: {output_pdf}")

    if len(merger.pages) > 0:
        merger.write(output_pdf)
        merger.close()
    else:
        merger.close()
        # No eliminamos temp_dir aquí para evitar borrar el archivo final
        raise ValueError("No se encontraron archivos PDF válidos para compilar.")

    # Verificar que el archivo final existe antes de continuar
    if not os.path.exists(output_pdf):
        print(f"Error: archivo final no encontrado: {output_pdf}")
        # No eliminamos temp_dir aquí para evitar borrar el archivo final
        raise FileNotFoundError(f"Archivo final no encontrado: {output_pdf}")

    size_bytes = os.path.getsize(output_pdf)
    print(f"Tamaño archivo final: {size_bytes} bytes")

    if size_bytes < 3 * 1024 * 1024:
        compression_level = "none"
    elif size_bytes < 8 * 1024 * 1024:
        compression_level = "ebook"
    else:
        compression_level = "screen"

    compressed_pdf = os.path.join(temp_dir, "temp_compressed.pdf")
    print(f"Archivo PDF comprimido temporal: {compressed_pdf}")
    final_pdf = compress_pdf(output_pdf, compressed_pdf, compression_level=compression_level)

    print(f"compress_pdf devolvió: {final_pdf}")
    print(f"¿Existe archivo final? {os.path.exists(final_pdf)}")

    # Si se creó un archivo comprimido, reemplazamos el original y devolvemos la ruta correcta
    if final_pdf != output_pdf:
        os.replace(final_pdf, output_pdf)
        final_path = output_pdf
    else:
        final_path = output_pdf

    # NO eliminamos temp_dir aquí para evitar borrar el archivo final
    # La eliminación se hará después de mover el archivo final en run_compilation

    # Devolvemos la ruta del archivo final y la carpeta temporal para eliminarla luego
    return final_path, temp_dir


def select_files():
    """
    Abre un diálogo para seleccionar múltiples archivos y guarda la lista globalmente.
    Muestra en el Entry la cantidad de archivos seleccionados.
    """
    global selected_files, selected_mode
    selected_files = filedialog.askopenfilenames(
        title="Selecciona los archivos a compilar",
        filetypes=[
            ("Todos los archivos", "*.*"),
            ("Archivos PDF", "*.pdf"),
            ("Archivos de texto", "*.txt"),
            ("Archivos Word", "*.docx"),
            ("Imágenes", "*.png;*.jpg;*.jpeg")
        ]
    )
    if selected_files:
        entry_dir.delete(0, tk.END)
        entry_dir.insert(0, f"{len(selected_files)} archivos seleccionados")
        selected_mode = "files"


def run_compilation():
    """
    Ejecuta la compilación según el modo seleccionado (carpeta o archivos).
    Mueve el PDF final a la carpeta Descargas con nombre adecuado. 
    Elimina la carpeta temporal solo después de mover el archivo final.
    """
    global selected_mode, selected_files
    input_value = entry_dir.get()
    if not input_value:
        messagebox.showerror("Error", "Por favor, selecciona una carpeta o archivos válidos.")
        return
    try:
        btn_compile.config(state=tk.DISABLED)
        if selected_mode == "folder":
            output_pdf = compile_pdfs_in_directory(input_value)
            downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
            dir_name = os.path.basename(os.path.normpath(input_value))
            output_pdf_dest = os.path.join(downloads_path, f"{dir_name}_UNIDO.pdf")
            if os.path.exists(output_pdf_dest):
                os.remove(output_pdf_dest)
            print(f"Moviendo archivo final de {output_pdf} a {output_pdf_dest}")
            if not os.path.exists(output_pdf):
                print(f"Error: archivo final no existe: {output_pdf}")
            else:
                shutil.move(output_pdf, output_pdf_dest)
            output_pdf = output_pdf_dest
        elif selected_mode == "files":
            if not selected_files:
                messagebox.showerror("Error", "No hay archivos seleccionados.")
                return
            # Ahora recibimos también la carpeta temporal para eliminarla después
            output_pdf, temp_dir = compile_pdfs_from_files(selected_files)
            downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
            base_name = "Documentos_UNIDOS"
            i = 1
            while True:
                candidate = os.path.join(downloads_path, f"{base_name}_{i}.pdf")
                if not os.path.exists(candidate):
                    output_pdf_dest = candidate
                    break
                i += 1
            print(f"Moviendo archivo final de {output_pdf} a {output_pdf_dest}")
            if not os.path.exists(output_pdf):
                print(f"Error: archivo final no existe: {output_pdf}")
            else:
                shutil.move(output_pdf, output_pdf_dest)
            # Eliminamos la carpeta temporal solo después de mover el archivo final
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                print(f"Error eliminando directorio temporal {temp_dir}: {e}")
            output_pdf = output_pdf_dest
        else:
            messagebox.showerror("Error", "Modo de selección desconocido.")
            return

        messagebox.showinfo("Éxito", f"PDF generado:\n{output_pdf}")
        try:
            os.startfile(output_pdf)
        except Exception as e:
            print(f"No se pudo abrir el archivo: {e}")
    except Exception as e:
        messagebox.showerror("Error", f"Ocurrió un error:\n{e}")
    finally:
        btn_compile.config(state=tk.NORMAL)


root = tk.Tk()
root.title("Compilador de PDFs")
root.geometry("600x150")
root.resizable(False, False)

lbl = tk.Label(root, text="Selecciona el directorio con archivos a compilar:")
lbl.pack(pady=10)

frame = tk.Frame(root)
frame.pack(pady=5, padx=10, fill="x")

entry_dir = tk.Entry(frame, width=50)
entry_dir.pack(side=tk.LEFT, fill="x", expand=True)


def select_directory():
    """
    Abre un diálogo para seleccionar una carpeta y actualiza el Entry y modo.
    """
    global selected_mode
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        entry_dir.delete(0, tk.END)
        entry_dir.insert(0, folder_selected)
        selected_mode = "folder"


btn_browse_folder = tk.Button(frame, text="Seleccionar Carpeta", command=select_directory)
btn_browse_folder.pack(side=tk.LEFT, padx=5)

btn_browse_files = tk.Button(frame, text="Seleccionar Archivos", command=select_files)
btn_browse_files.pack(side=tk.LEFT, padx=5)

btn_compile = tk.Button(root, text="Compilar PDFs", command=run_compilation, width=20)
btn_compile.pack(pady=15)

root.mainloop()
