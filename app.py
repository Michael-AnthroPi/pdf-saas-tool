import os
import shutil
from flask import Flask, render_template, request, send_file, flash, redirect, url_for
from werkzeug.utils import secure_filename
from utils import merge_pdfs, split_pdf, pdf_to_images

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev_key_secret_123')

# Configuration des dossiers temporaires (compatibles Cloud/Docker)
UPLOAD_FOLDER = '/tmp/uploads'
OUTPUT_FOLDER = '/tmp/outputs'

# Nettoyage et création au démarrage
for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER]:
    if os.path.exists(folder):
        shutil.rmtree(folder)
    os.makedirs(folder, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

# Définition des outils (Menu)
TOOLS = {
    'organise': [
        {'id': 'merge', 'name': 'Fusionner', 'icon': 'bi-files', 'desc': 'Combiner plusieurs PDF en un seul.'},
        {'id': 'split', 'name': 'Diviser', 'icon': 'bi-scissors', 'desc': 'Extraire les pages d\'un PDF.'},
    ],
    'convert_from': [
        {'id': 'pdf_to_img', 'name': 'PDF en Image', 'icon': 'bi-images', 'desc': 'Convertir chaque page en JPG.'},
    ]
}

@app.route('/')
def dashboard():
    return render_template('dashboard.html', tools=TOOLS)

@app.route('/tool/<tool_id>', methods=['GET', 'POST'])
def tool_view(tool_id):
    # Trouver l'outil sélectionné
    current_tool = None
    for category in TOOLS.values():
        for tool in category:
            if tool['id'] == tool_id:
                current_tool = tool
                break
    
    if not current_tool:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        if 'files' not in request.files:
            flash('Aucun fichier.')
            return redirect(request.url)
        
        files = request.files.getlist('files')
        if not files or files[0].filename == '':
            flash('Sélectionnez un fichier valide.')
            return redirect(request.url)

        # Sauvegarde des fichiers
        saved_paths = []
        try:
            # Nettoyage préalable du dossier upload pour éviter les mélanges
            for f in os.listdir(app.config['UPLOAD_FOLDER']):
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], f))

            for file in files:
                filename = secure_filename(file.filename)
                path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(path)
                saved_paths.append(path)

            # --- ROUTAGE LOGIQUE ---
            output_file = None
            
            if tool_id == 'merge':
                if len(saved_paths) < 2:
                    flash('Il faut au moins 2 fichiers pour fusionner.')
                    return redirect(request.url)
                output_file = merge_pdfs(saved_paths, app.config['OUTPUT_FOLDER'])
                
            elif tool_id == 'split':
                output_file = split_pdf(saved_paths[0], app.config['OUTPUT_FOLDER'])
                
            elif tool_id == 'pdf_to_img':
                output_file = pdf_to_images(saved_paths[0], app.config['OUTPUT_FOLDER'])

            if output_file:
                return send_file(output_file, as_attachment=True)
                
        except Exception as e:
            print(f"Erreur: {e}")
            flash(f"Une erreur est survenue : {str(e)}")
            return redirect(request.url)

    return render_template('tool.html', tool=current_tool)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
