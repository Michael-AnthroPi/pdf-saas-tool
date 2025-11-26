import os
import zipfile
import subprocess
from PyPDF2 import PdfReader, PdfWriter
from pdf2image import convert_from_path
from PIL import Image
from pdf2docx import Converter

# --- FONCTIONS EXISTANTES ---

def merge_pdfs(file_paths, output_folder):
    merger = PdfWriter()
    for pdf in file_paths:
        merger.append(pdf)
    output_path = os.path.join(output_folder, 'fusion_resultat.pdf')
    merger.write(output_path)
    merger.close()
    return output_path

def split_pdf(file_path, output_folder):
    reader = PdfReader(file_path)
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    zip_path = os.path.join(output_folder, f'{base_name}_split.zip')
    
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for i, page in enumerate(reader.pages):
            writer = PdfWriter()
            writer.add_page(page)
            temp_pdf = os.path.join(output_folder, f"page_{i+1}.pdf")
            with open(temp_pdf, 'wb') as f:
                writer.write(f)
            zipf.write(temp_pdf, f"page_{i+1}.pdf")
            os.remove(temp_pdf)
    return zip_path

def pdf_to_images(file_path, output_folder):
    images = convert_from_path(file_path)
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    zip_path = os.path.join(output_folder, f'{base_name}_images.zip')

    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for i, image in enumerate(images):
            img_name = f"page_{i+1}.jpg"
            img_path = os.path.join(output_folder, img_name)
            image.save(img_path, 'JPEG')
            zipf.write(img_path, img_name)
            os.remove(img_path)
    return zip_path

def images_to_pdf(image_paths, output_folder):
    images = []
    for path in image_paths:
        img = Image.open(path)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        images.append(img)
    
    output_path = os.path.join(output_folder, 'images_converties.pdf')
    if images:
        images[0].save(output_path, save_all=True, append_images=images[1:])
    return output_path

def rotate_pdf(file_path, output_folder):
    reader = PdfReader(file_path)
    writer = PdfWriter()
    for page in reader.pages:
        page.rotate(90)
        writer.add_page(page) 
    output_path = os.path.join(output_folder, 'pivote.pdf')
    with open(output_path, 'wb') as f:
        writer.write(f)
    return output_path

def protect_pdf(file_path, password, output_folder):
    reader = PdfReader(file_path)
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    writer.encrypt(password)
    output_path = os.path.join(output_folder, 'protege.pdf')
    with open(output_path, 'wb') as f:
        writer.write(f)
    return output_path

# --- NOUVELLES FONCTIONS PRO ---

def compress_pdf(file_path, output_folder):
    """Utilise Ghostscript pour compresser le PDF"""
    output_path = os.path.join(output_folder, 'compresse.pdf')
    
    # Commande système Ghostscript
    # -dPDFSETTINGS=/ebook donne une bonne qualité pour une taille réduite
    # /screen est encore plus petit mais de basse qualité
    subprocess.call([
        'gs', '-sDEVICE=pdfwrite', '-dCompatibilityLevel=1.4',
        '-dPDFSETTINGS=/ebook', '-dNOPAUSE', '-dQUIET', '-dBATCH',
        f'-sOutputFile={output_path}', file_path
    ])
    
    return output_path

def pdf_to_word(file_path, output_folder):
    """Convertit PDF en DOCX avec pdf2docx"""
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    output_path = os.path.join(output_folder, f'{base_name}.docx')
    
    cv = Converter(file_path)
    cv.convert(output_path, start=0, end=None)
    cv.close()
    
    return output_path

def word_to_pdf(file_path, output_folder):
    """Utilise LibreOffice en mode 'headless' pour convertir DOCX en PDF"""
    # La commande libreoffice va créer le fichier dans output_folder
    # mais il garde le même nom de base.
    subprocess.run([
        'libreoffice', '--headless', '--convert-to', 'pdf',
        '--outdir', output_folder,
        file_path
    ], check=True)
    
    # On doit retrouver le nom du fichier généré
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    expected_output = os.path.join(output_folder, f'{base_name}.pdf')
    
    if os.path.exists(expected_output):
        return expected_output
    raise Exception("La conversion LibreOffice a échoué")
