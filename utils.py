import os
import zipfile
import subprocess
from PyPDF2 import PdfReader, PdfWriter
from pdf2image import convert_from_path
from PIL import Image

# ... (GARDE TOUTES LES FONCTIONS : merge_pdfs, split_pdf, pdf_to_images, images_to_pdf, rotate_pdf, protect_pdf) ...

# --- ON GARDE LA COMPRESSION (C'est léger) ---
def compress_pdf(file_path, output_folder):
    output_path = os.path.join(output_folder, 'compresse.pdf')
    subprocess.call([
        'gs', '-sDEVICE=pdfwrite', '-dCompatibilityLevel=1.4',
        '-dPDFSETTINGS=/ebook', '-dNOPAUSE', '-dQUIET', '-dBATCH',
        f'-sOutputFile={output_path}', file_path
    ])
    return output_path

# SUPPRIME LES FONCTIONS pdf_to_word ET word_to_pdf D'ICI

# utils.py - Ajoute ceci à la fin

def reorder_pdf(file_path, page_order, output_folder):
    """
    Reconstruit le PDF en suivant l'ordre donné par le Front-End.
    page_order est une liste de strings ou d'entiers : ['0', '2', '1']
    """
    reader = PdfReader(file_path)
    writer = PdfWriter()
    
    # page_order arrive souvent sous forme de string "0,2,1", il faut le parser si nécessaire
    if isinstance(page_order, str):
        page_order = [int(x) for x in page_order.split(',') if x.strip()]
        
    for page_num in page_order:
        # On vérifie que la page existe (sécurité)
        idx = int(page_num)
        if 0 <= idx < len(reader.pages):
            writer.add_page(reader.pages[idx])
            
    output_path = os.path.join(output_folder, 'organise.pdf')
    with open(output_path, 'wb') as f:
        writer.write(f)
    return output_path
