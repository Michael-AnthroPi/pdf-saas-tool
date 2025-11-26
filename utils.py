import os
import zipfile
from PyPDF2 import PdfReader, PdfWriter
from pdf2image import convert_from_path
from PIL import Image

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

# --- NOUVELLES FONCTIONS ---

def images_to_pdf(image_paths, output_folder):
    """Convertit une liste d'images (JPG/PNG) en un seul PDF"""
    images = []
    for path in image_paths:
        img = Image.open(path)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        images.append(img)
    
    output_path = os.path.join(output_folder, 'images_converties.pdf')
    # La première image sauvegarde, les autres sont ajoutées ("append")
    if images:
        images[0].save(output_path, save_all=True, append_images=images[1:])
    
    return output_path

def rotate_pdf(file_path, output_folder):
    """Pivote toutes les pages de 90 degrés"""
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
    """Ajoute un mot de passe au PDF"""
    reader = PdfReader(file_path)
    writer = PdfWriter()
    
    for page in reader.pages:
        writer.add_page(page)
    
    writer.encrypt(password)
    
    output_path = os.path.join(output_folder, 'protege.pdf')
    with open(output_path, 'wb') as f:
        writer.write(f)
    return output_path
