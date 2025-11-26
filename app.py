import os
import shutil
from flask import Flask, render_template, request, send_file, flash, redirect, url_for
from werkzeug.utils import secure_filename
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from utils import merge_pdfs, split_pdf, pdf_to_images

app = Flask(__name__)
# On utilise une clé secrète robuste (récupérée de Render ou par défaut pour le dev)
app.secret_key = os.environ.get('SECRET_KEY', 'dev_key_secret_123')

# --- CONFIGURATION LOGIN ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # Redirige ici si non connecté

# Une classe utilisateur simple (sans base de données)
class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# --- CONFIGURATION FICHIERS ---
UPLOAD_FOLDER = '/tmp/uploads'
OUTPUT_FOLDER = '/tmp/outputs'

for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER]:
    if os.path.exists(folder):
        shutil.rmtree(folder)
    os.makedirs(folder, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

TOOLS = {
    'organise': [
        {'id': 'merge', 'name': 'Fusionner', 'icon': 'bi-files', 'desc': 'Combiner plusieurs PDF en un seul.'},
        {'id': 'split', 'name': 'Diviser', 'icon': 'bi-scissors', 'desc': 'Extraire les pages d\'un PDF.'},
    ],
    'convert_from': [
        {'id': 'pdf_to_img', 'name': 'PDF en Image', 'icon': 'bi-images', 'desc': 'Convertir chaque page en JPG.'},
    ]
}

# --- ROUTES ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Récupération des identifiants sécurisés depuis Render
        # Si pas définis sur Render, par défaut c'est admin/admin
        env_user = os.environ.get('ADMIN_USER', 'admin')
        env_pass = os.environ.get('ADMIN_PASSWORD', 'admin')

        if username == env_user and password == env_pass:
            user = User(id=username)
            login_user(user)
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
@login_required  # <--- PROTECTION ACTIVÉE
def dashboard():
    return render_template('dashboard.html', tools=TOOLS)

@app.route('/tool/<tool_id>', methods=['GET', 'POST'])
@login_required  # <--- PROTECTION ACTIVÉE
def tool_view(tool_id):
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

        saved_paths = []
        try:
            # Nettoyage
            for f in os.listdir(app.config['UPLOAD_FOLDER']):
                path = os.path.join(app.config['UPLOAD_FOLDER'], f)
                if os.path.isfile(path):
                    os.remove(path)

            for file in files:
                filename = secure_filename(file.filename)
                path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(path)
                saved_paths.append(path)

            output_file = None
            if tool_id == 'merge':
                if len(saved_paths) < 2:
                    flash('Il faut au moins 2 fichiers.')
                    return redirect(request.url)
                output_file = merge_pdfs(saved_paths, app.config['OUTPUT_FOLDER'])
            elif tool_id == 'split':
                output_file = split_pdf(saved_paths[0], app.config['OUTPUT_FOLDER'])
            elif tool_id == 'pdf_to_img':
                output_file = pdf_to_images(saved_paths[0], app.config['OUTPUT_FOLDER'])

            if output_file:
                return send_file(output_file, as_attachment=True)
                
        except Exception as e:
            flash(f"Erreur : {str(e)}")
            return redirect(request.url)

    return render_template('tool.html', tool=current_tool)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
