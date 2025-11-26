import os
import zipfile
from PyPDF2 import PdfReader, PdfWriter
from pdf2image import convert_from_path

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
    # Sur Docker/Linux, poppler est dans le PATH, pas besoin de spécifier le chemin
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
