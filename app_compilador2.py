import sys
import os
import subprocess
import time
import shutil
import tempfile
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# Dependencias externas
try:
    from PIL import Image, ImageTk
    import docx2txt  # Usar docx2txt para extraer texto plano sin dependencias pesadas
    from docx2pdf import convert
    from fpdf import FPDF  # Usar fpdf original (con workarounds para UTF-8)
    from PyPDF2 import PdfMerger, PdfReader, PdfWriter
    from PyPDF2.errors import PdfReadError
except ImportError as e:
    messagebox.showerror("Error", f"Faltan dependencias: {e}. Instala con pip.")
    sys.exit(1)

# Constantes para configuraciones
SUPPORTED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".txt", ".docx"}
COMPRESSION_LEVELS = {0: "none", 1: "ebook", 2: "screen"}
ENCODINGS = ["utf-8", "latin-1", "cp1252", "iso-8859-1"]
GS_EXECUTABLE_REL = "DistribucionApp/gs/gs10.05.1/bin/gswin64c.exe"

# Variables globales
selected_mode = None
selected_files = []

def check_dependencies():
    """Verifica dependencias críticas al inicio."""
    if not os.path.exists(os.path.join(os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__), GS_EXECUTABLE_REL)):
        messagebox.showwarning("Advertencia", "Ghostscript no encontrado. La compresión no funcionará.")
    try:
        docx2txt.process.__doc__  # Verificar docx2txt
    except:
        messagebox.showwarning("Advertencia", "docx2txt no funciona. Instala con pip install docx2txt.")

def get_resource_path(relative_path):
    """Obtiene ruta absoluta para recursos (funciona en script y EXE)."""
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

def txt_to_pdf(text_path, pdf_path):
    """Convierte TXT a PDF con soporte para caracteres especiales (workaround UTF-8)."""
    try:
        content = ""
        for enc in ENCODINGS:
            try:
                with open(text_path, "r", encoding=enc) as f:
                    content = f.read()
                if content.strip():
                    break
            except UnicodeDecodeError:
                continue
        if not content.strip():
            content = f"Archivo TXT vacío: {os.path.basename(text_path)}"
        
        # Workaround para UTF-8: Reemplazar caracteres no soportados por latin-1
        content_safe = content.encode('latin-1', 'replace').decode('latin-1')
        
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", size=12)  # Usar fuente core para evitar warning
        pdf.multi_cell(0, 10, content_safe)
        pdf.output(pdf_path)
    except Exception as e:
        print(f"Error en TXT {text_path}: {e}")
        raise

def docx_to_pdf(archivo_docx, pdf_path):
    try:
        convert(archivo_docx, pdf_path)
        print(f"Convertido {archivo_docx} a {pdf_path} con formato preservado.")
    except Exception as e:
        print(f"Error con docx2pdf: {e}. Usando fallback a texto plano.")
        try:
            from docx2txt import process as docx2txt_process
            texto = docx2txt_process(archivo_docx)
            pdf = FPDF()
            pdf.add_page()
            pdf.add_font('DejaVu', '', 'DejaVuSans.ttf', uni=True)  # Fuente Unicode
            pdf.set_font('DejaVu', '', 12)
            pdf.multi_cell(0, 10, texto.encode('latin-1', 'replace').decode('latin-1'))  # Manejo básico de Unicode
            pdf.output(pdf_path)
            print(f"Fallback completado para {archivo_docx}.")
        except Exception as e2:
            print(f"Fallback también falló: {e2}")

        
def image_to_pdf(image_path, pdf_path):
    """Convierte imagen a PDF."""
    try:
        image = Image.open(image_path)
        if image.mode == "RGBA":
            image = image.convert("RGB")
        image.save(pdf_path, "PDF", resolution=100.0)
    except Exception as e:
        print(f"Error en imagen {image_path}: {e}")
        raise

def clean_pdf(input_path, output_path):
    """Limpia PDF."""
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
        print(f"PDF corrupto {input_path}: {e}")
        return False

def compress_pdf(input_path, output_path, compression_level="none"):
    """Comprime PDF con Ghostscript."""
    if compression_level == "none":
        return input_path

    base_path = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__)
    gs_executable = os.path.join(base_path, GS_EXECUTABLE_REL)
    if not os.path.exists(gs_executable):
        print("Ghostscript no encontrado.")
        return input_path

    pdf_setting = {"ebook": "/ebook", "screen": "/screen"}.get(compression_level, "/screen")
    args = [
        gs_executable, "-sDEVICE=pdfwrite", "-dCompatibilityLevel=1.4",
        f"-dPDFSETTINGS={pdf_setting}", "-dNOPAUSE", "-dQUIET", "-dBATCH",
        f"-sOutputFile={output_path}", input_path
    ]
    try:
        creation_flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        subprocess.run(args, check=True, creationflags=creation_flags)
        if os.path.exists(output_path) and os.path.getsize(output_path) < os.path.getsize(input_path):
            return output_path
        else:
            if os.path.exists(output_path):
                os.remove(output_path)
            return input_path
    except Exception as e:
        print(f"Error en compresión: {e}")
        return input_path

def process_file(filepath, temp_dir):
    """Procesa un archivo individual y retorna la ruta del PDF temporal."""
    name, ext = os.path.splitext(os.path.basename(filepath))
    ext = ext.lower()
    temp_pdf = os.path.join(temp_dir, f"{name}_temp.pdf")

    try:
        if ext == ".pdf":
            if clean_pdf(filepath, temp_pdf):
                return temp_pdf
        elif ext in [".png", ".jpg", ".jpeg"]:
            image_to_pdf(filepath, temp_pdf)
            return temp_pdf
        elif ext == ".txt":
            txt_to_pdf(filepath, temp_pdf)
            return temp_pdf
        elif ext == ".docx":
            docx_to_pdf(filepath, temp_pdf)
            return temp_pdf
        else:
            print(f"Extensión no soportada: {ext}")
    except Exception as e:
        print(f"Error procesando {filepath}: {e}")
    return None

def compile_pdfs(files_or_directory, is_directory=False):
    """Función unificada para compilar PDFs desde archivos o directorio."""
    temp_dir = tempfile.mkdtemp(prefix="temp_pdfs_")
    merger = PdfMerger()

    if is_directory:
        files = [os.path.join(files_or_directory, f) for f in os.listdir(files_or_directory) if os.path.splitext(f)[1].lower() in SUPPORTED_EXTENSIONS]
    else:
        files = files_or_directory

    for filepath in files:
        temp_pdf = process_file(filepath, temp_dir)
        if temp_pdf:
            merger.append(temp_pdf)

    if len(merger.pages) == 0:
        merger.close()
        shutil.rmtree(temp_dir)
        raise ValueError("No se encontraron archivos válidos.")

    output_pdf = os.path.join(temp_dir, "output.pdf")
    merger.write(output_pdf)
    merger.close()

    size_bytes = os.path.getsize(output_pdf)
    compression_level = COMPRESSION_LEVELS.get(min(2, size_bytes // (3 * 1024 * 1024)), "none")
    compressed_pdf = os.path.join(temp_dir, "compressed.pdf")
    final_pdf = compress_pdf(output_pdf, compressed_pdf, compression_level)
    if final_pdf != output_pdf:
        os.replace(final_pdf, output_pdf)

    return output_pdf, temp_dir

def select_files():
    global selected_files, selected_mode
    selected_files = filedialog.askopenfilenames(
        title="Selecciona archivos", filetypes=[("Archivos", "*.*")]
    )
    if selected_files:
        entry_dir.delete(0, tk.END)
        entry_dir.insert(0, f"{len(selected_files)} archivos")
        selected_mode = "files"

def select_directory():
    global selected_mode
    folder = filedialog.askdirectory()
    if folder:
        entry_dir.delete(0, tk.END)
        entry_dir.insert(0, folder)
        selected_mode = "folder"

def abrir_ayuda():
    ruta_ayuda = get_resource_path("ayuda.pdf")
    try:
        os.startfile(ruta_ayuda)
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo abrir ayuda: {e}")

def run_compilation():
    global selected_mode, selected_files
    input_value = entry_dir.get()
    if not input_value:
        messagebox.showerror("Error", "Selecciona archivos o carpeta.")
        return

    try:
        btn_compile.config(state="disabled")
        if selected_mode == "folder":
            output_pdf, temp_dir = compile_pdfs(input_value, is_directory=True)
            # Nombre para carpeta: usar dir_name
            dir_name = os.path.basename(os.path.normpath(input_value))
            dest = os.path.join(os.path.expanduser("~"), "Downloads", f"1_{dir_name}_UNIDO.pdf")
        elif selected_mode == "files":
            if not selected_files:
                raise ValueError("No hay archivos.")
            output_pdf, temp_dir = compile_pdfs(selected_files)
            # Nombre para archivos: usar contador
            downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
            base_name = "1_Documentos_UNIDOS"
            i = 1
            while True:
                dest = os.path.join(downloads_path, f"{base_name}_{i}.pdf")
                if not os.path.exists(dest):
                    break
                i += 1
        else:
            raise ValueError("Modo desconocido.")

        # Mover a Descargas (común para ambos)
        if os.path.exists(dest):
            os.remove(dest)  # Sobrescribir si existe
        shutil.move(output_pdf, dest)
        shutil.rmtree(temp_dir)

        messagebox.showinfo("Éxito", f"PDF generado: {dest}")
        os.startfile(dest)
    except Exception as e:
        messagebox.showerror("Error", f"Error: {e}")
    finally:
        btn_compile.config(state="normal")

# GUI
check_dependencies()
root = tk.Tk()
root.title("Compilador de PDFs")
root.geometry("600x130")
root.resizable(False, False)

lbl = tk.Label(root, text="Selecciona carpeta o archivos:")
lbl.pack(pady=10)

frame = tk.Frame(root)
frame.pack(pady=5, padx=10, fill="x")

entry_dir = tk.Entry(frame, width=50)
entry_dir.pack(side="left", fill="x", expand=True)

btn_browse_folder = tk.Button(frame, text="Carpeta", command=select_directory)
btn_browse_folder.pack(side="left", padx=5)

btn_browse_files = tk.Button(frame, text="Archivos", command=select_files)
btn_browse_files.pack(side="left", padx=5)

btn_compile = tk.Button(root, text="Compilar PDF", command=run_compilation, width=20)
btn_compile.pack(pady=5)

# Botón ayuda con ícono
icono_ayuda = None
try:
    ayuda_png = get_resource_path("ayuda.png")
    imagen = Image.open(ayuda_png)
    imagen = imagen.resize((24, 24), Image.Resampling.LANCZOS)
    icono_ayuda = ImageTk.PhotoImage(imagen)
except Exception as e:
    print(f"Error cargando ícono: {e}")

btn_ayuda = tk.Button(root, image=icono_ayuda, command=abrir_ayuda)
if icono_ayuda:
    btn_ayuda.image = icono_ayuda
btn_ayuda.place(relx=1.0, rely=0.1, anchor="se", x=-10, y=20)

# Ícono ventana
try:
    icon_path = get_resource_path("icono.ico")
    if os.path.exists(icon_path):
        root.iconbitmap(icon_path)
except Exception as e:
    print(f"Error ícono ventana: {e}")

root.mainloop()
