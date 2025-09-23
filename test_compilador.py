import os
import shutil
from app_compilador import compile_pdfs_in_directory

# Crear directorio de prueba
test_dir = "test_input"
os.makedirs(test_dir, exist_ok=True)

# Crear archivo de texto de prueba
with open(os.path.join(test_dir, "test.txt"), "w", encoding="utf-8") as f:
    f.write("Este es un archivo de texto de prueba para compilar en PDF.")

# Crear archivo DOCX de prueba (simple)
from docx import Document
doc = Document()
doc.add_paragraph("Este es un documento Word de prueba.")
doc.save(os.path.join(test_dir, "test.docx"))

# Crear imagen de prueba (simple)
from PIL import Image
img = Image.new('RGB', (100, 100), color = 'red')
img.save(os.path.join(test_dir, "test.png"))

print("Archivos de prueba creados.")

try:
    output_pdf = compile_pdfs_in_directory(test_dir)
    print(f"PDF generado: {output_pdf}")

    if os.path.exists(output_pdf):
        print("✓ PDF creado exitosamente.")
        size = os.path.getsize(output_pdf)
        print(f"Tamaño del PDF: {size} bytes")

        # Verificar que el directorio temporal fue eliminado
        base_path = os.path.dirname(os.path.abspath(__file__))
        temp_dir = os.path.join(base_path, "temp_pdfs_compilador")
        if not os.path.exists(temp_dir):
            print("✓ Directorio temporal eliminado correctamente.")
        else:
            print("✗ Directorio temporal no fue eliminado.")

        # Intentar abrir el PDF
        try:
            os.startfile(output_pdf)
            print("✓ PDF abierto en el visor por defecto.")
        except Exception as e:
            print(f"✗ Error al abrir PDF: {e}")

    else:
        print("✗ PDF no fue creado.")

except Exception as e:
    print(f"Error durante la compilación: {e}")

# Limpiar archivos de prueba
shutil.rmtree(test_dir)
if os.path.exists(output_pdf):
    os.remove(output_pdf)
print("Archivos de prueba limpiados.")
