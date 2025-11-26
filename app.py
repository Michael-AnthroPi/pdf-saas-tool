import os
import shutil
from flask import Flask, render_template, request, send_file, flash, redirect, url_for
from werkzeug.utils import secure_filename
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

# On importe toutes nos fonctions depuis utils.py
# Note : On a retiré les fonctions Word pour économiser la RAM
from utils import (
    merge_pdfs, split_pdf, pdf_to_images, rotate_pdf, 
    images_to_pdf, protect_pdf, compress_pdf, reorder_pdf
)

app = Flask(__name__)
# Clé secrète pour la sécurité (à changer en production via variables d'environnement)
app.secret_key = os.environ.get('SECRET_KEY', 'dev_key_secret_123')

# --- CONFIGURATION LOGIN ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# --- CONFIGURATION FICHIERS ---
UPLOAD_FOLDER = '/tmp/uploads'
OUTPUT_FOLDER = '/tmp/outputs'

# Nettoyage au démarrage
for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER]:
    if os.path.exists(folder):
        shutil.rmtree(folder)
    os.makedirs(folder, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

# --- LISTE DES OUTILS ---
TOOLS = {
    'popular': [
        {'id': 'merge', 'name': 'Fusionner PDF', 'icon': 'bi-arrows-angle-contract', 'color': 'text-danger', 'desc': 'Combiner des PDF dans l\'ordre de votre choix.'},
        {'id': 'split', 'name': 'Diviser PDF', 'icon': 'bi-scissors', 'color': 'text-danger', 'desc': 'Séparer une page ou extraire des pages.'},
        {'id': 'compress', 'name': 'Compresser PDF', 'icon': 'bi-arrow-down-right-square', 'color': 'text-success', 'desc': 'Réduire la taille de votre fichier PDF.'}, 
    ],
    'convert': [
        {'id': 'pdf_to_img', 'name': 'PDF en JPG', 'icon': 'bi-file-image', 'color': 'text-warning', 'desc': 'Extraire toutes les images ou pages en JPG.'},
        {'id': 'img_to_pdf', 'name': 'JPG en PDF', 'icon': 'bi-images', 'color': 'text-warning', 'desc': 'Convertir vos images JPG/PNG en un document PDF.'},
    ],
    'security': [
        {'id': 'protect', 'name': 'Protéger PDF', 'icon': 'bi-shield-lock', 'color': 'text-dark', 'desc': 'Chiffrer votre PDF avec un mot de passe.'},
        {'id': 'unlock', 'name': 'Déverrouiller', 'icon': 'bi-unlock', 'color': 'text-dark', 'desc': 'Retirer le mot de passe.'},
    ],
    'edit': [
        {'id': 'organize', 'name': 'Organiser PDF', 'icon': 'bi-grid-3x3', 'color': 'text-danger', 'desc': 'Trier visuellement, supprimer et réorganiser des pages.'},
        {'id': 'rotate', 'name': 'Pivoter PDF', 'icon': 'bi-arrow-clockwise', 'color': 'text-info', 'desc': 'Faites pivoter vos pages PDF.'},
    ]
}

def get_tool_by_id(tool_id):
    for category in TOOLS.values():
        for tool in category:
            if tool['id'] == tool_id:
                return tool
    return None

# --- ROUTES ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        # Récupère les identifiants depuis Render (Environment Variables)
        env_user = os.environ.get('ADMIN_USER', 'admin')
        env_pass = os.environ.get('ADMIN_PASSWORD', 'admin')

        if username == env_user and password == env_pass:
            login_user(User(id=username))
            return redirect(url_for('dashboard'))
        else:
            flash('Identifiants incorrects.')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def dashboard():
    return render_template('dashboard.html', tools=TOOLS)

# --- ROUTE SPÉCIALE : ORGANISATEUR VISUEL ---
@app.route('/tool/organize', methods=['GET', 'POST'])
@login_required
def organize_tool():
    # Affichage de l'interface (GET)
    if request.method == 'GET':
        return render_template('organizer.html')

    # Traitement du fichier trié (POST)
    if request.method == 'POST':
        if 'file_reupload' not in request.files:
            flash('Erreur de fichier.')
            return redirect(request.url)
        
        file = request.files['file_reupload']
        page_order = request.form.get('page_order') # ex: "0,3,1"
        
        if not file or not page_order:
            flash('Erreur de données.')
            return redirect(request.url)

        try:
            filename = secure_filename(file.filename)
            upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(upload_path)

            # Appel de la fonction de réorganisation
            output_file = reorder_pdf(upload_path, page_order, app.config['OUTPUT_FOLDER'])
            
            return send_file(output_file, as_attachment=True, download_name=f"organise_{filename}")

        except Exception as e:
            flash(f"Erreur : {e}")
            return redirect(request.url)

# --- ROUTE GÉNÉRIQUE : AUTRES OUTILS ---
@app.route('/tool/<tool_id>', methods=['GET', 'POST'])
@login_required
def tool_view(tool_id):
    # Si l'utilisateur clique sur Organiser, on le redirige vers la route spéciale
    if tool_id == 'organize':
        return redirect(url_for('organize_tool'))

    tool = get_tool_by_id(tool_id)
    if not tool:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        user_password = request.form.get('user_password', None)
        
        if 'files' not in request.files:
            flash('Aucun fichier.')
            return redirect(request.url)
        
        files = request.files.getlist('files')
        if not files or files[0].filename == '':
            flash('Sélectionnez un fichier.')
            return redirect(request.url)

        saved_paths = []
        try:
            # Nettoyage du dossier temporaire
            for f in os.listdir(app.config['UPLOAD_FOLDER']):
                try:
                    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], f))
                except: pass

            for file in files:
                filename = secure_filename(file.filename)
                path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(path)
                saved_paths.append(path)

            output_file = None
            
            # --- LOGIQUE DES OUTILS ---
            if tool_id == 'merge':
                if len(saved_paths) < 2:
                    flash('Il faut au moins 2 fichiers.')
                    return redirect(request.url)
                output_file = merge_pdfs(saved_paths, app.config['OUTPUT_FOLDER'])
            
            elif tool_id == 'split':
                output_file = split_pdf(saved_paths[0], app.config['OUTPUT_FOLDER'])
            
            elif tool_id == 'pdf_to_img':
                output_file = pdf_to_images(saved_paths[0], app.config['OUTPUT_FOLDER'])
            
            elif tool_id == 'img_to_pdf':
                output_file = images_to_pdf(saved_paths, app.config['OUTPUT_FOLDER'])
            
            elif tool_id == 'rotate':
                output_file = rotate_pdf(saved_paths[0], app.config['OUTPUT_FOLDER'])
            
            elif tool_id == 'protect':
                if not user_password:
                    flash('Mot de passe requis.')
                    return redirect(request.url)
                output_file = protect_pdf(saved_paths[0], user_password, app.config['OUTPUT_FOLDER'])
                
            elif tool_id == 'compress':
                output_file = compress_pdf(saved_paths[0], app.config['OUTPUT_FOLDER'])

            else:
                flash("Outil non implémenté.")
                return redirect(request.url)

            if output_file:
                return send_file(output_file, as_attachment=True)
                
        except Exception as e:
            flash(f"Erreur : {str(e)}")
            return redirect(request.url)

    # Gestion des types de fichiers acceptés dans l'input HTML
    accept_types = ".pdf"
    if tool_id == 'img_to_pdf': accept_types = ".jpg, .jpeg, .png"
    
    return render_template('tool.html', tool=tool, accept_types=accept_types)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
