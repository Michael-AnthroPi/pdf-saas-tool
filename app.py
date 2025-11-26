# ... (Gardez les imports du haut comme avant) ...
from utils import (
    merge_pdfs, split_pdf, pdf_to_images, rotate_pdf, 
    images_to_pdf, protect_pdf, compress_pdf, pdf_to_word, word_to_pdf
)

# ... (Gardez la config Flask et Login comme avant) ...

# --- LISTE MISE À JOUR ---
TOOLS = {
    'popular': [
        {'id': 'merge', 'name': 'Fusionner PDF', 'icon': 'bi-arrows-angle-contract', 'color': 'text-danger', 'desc': 'Combiner des PDF dans l\'ordre de votre choix.'},
        {'id': 'split', 'name': 'Diviser PDF', 'icon': 'bi-scissors', 'color': 'text-danger', 'desc': 'Séparer une page ou extraire des pages.'},
        {'id': 'compress', 'name': 'Compresser PDF', 'icon': 'bi-arrow-down-right-square', 'color': 'text-success', 'desc': 'Réduire la taille de votre fichier PDF.'}, 
    ],
    'convert_pdf': [
        {'id': 'pdf_to_img', 'name': 'PDF en JPG', 'icon': 'bi-file-image', 'color': 'text-warning', 'desc': 'Extraire toutes les images ou pages en JPG.'},
        {'id': 'pdf_to_word', 'name': 'PDF en Word', 'icon': 'bi-file-word', 'color': 'text-primary', 'desc': 'Convertir facilement vos PDF en documents DOCX éditables.'},
    ],
    'convert_to_pdf': [
        {'id': 'img_to_pdf', 'name': 'JPG en PDF', 'icon': 'bi-images', 'color': 'text-warning', 'desc': 'Convertir vos images JPG/PNG en un document PDF.'},
        {'id': 'word_to_pdf', 'name': 'Word en PDF', 'icon': 'bi-file-earmark-word', 'color': 'text-primary', 'desc': 'Convertir DOCX en PDF.'},
    ],
    'security': [
        {'id': 'protect', 'name': 'Protéger PDF', 'icon': 'bi-shield-lock', 'color': 'text-dark', 'desc': 'Chiffrer votre PDF avec un mot de passe.'},
        {'id': 'unlock', 'name': 'Déverrouiller', 'icon': 'bi-unlock', 'color': 'text-dark', 'desc': 'Retirer le mot de passe (si vous l\'avez).'},
    ],
    'edit': [
        {'id': 'rotate', 'name': 'Pivoter PDF', 'icon': 'bi-arrow-clockwise', 'color': 'text-info', 'desc': 'Faites pivoter vos pages PDF.'},
        {'id': 'organize', 'name': 'Organiser PDF', 'icon': 'bi-grid-3x3', 'color': 'text-danger', 'desc': 'Trier ou supprimer des pages (Bientôt).'},
    ]
}

# ... (Gardez les fonctions get_tool_by_id, login, logout, dashboard comme avant) ...

@app.route('/tool/<tool_id>', methods=['GET', 'POST'])
@login_required
def tool_view(tool_id):
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
            # Nettoyage
            for f in os.listdir(app.config['UPLOAD_FOLDER']):
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], f))

            for file in files:
                filename = secure_filename(file.filename)
                path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(path)
                saved_paths.append(path)

            output_file = None
            
            # --- ROUTAGE COMPLET ---
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
                
            # --- NOUVEAUX OUTILS ---
            elif tool_id == 'compress':
                output_file = compress_pdf(saved_paths[0], app.config['OUTPUT_FOLDER'])
                
            elif tool_id == 'pdf_to_word':
                output_file = pdf_to_word(saved_paths[0], app.config['OUTPUT_FOLDER'])
                
            elif tool_id == 'word_to_pdf':
                output_file = word_to_pdf(saved_paths[0], app.config['OUTPUT_FOLDER'])

            else:
                flash("Outil non implémenté.")
                return redirect(request.url)

            if output_file:
                return send_file(output_file, as_attachment=True)
                
        except Exception as e:
            flash(f"Erreur : {str(e)}")
            return redirect(request.url)

    # Mise à jour de l'acceptation de fichier pour Word
    accept_types = ".pdf"
    if tool_id == 'img_to_pdf': accept_types = ".jpg, .jpeg, .png"
    if tool_id == 'word_to_pdf': accept_types = ".docx, .doc"
    
    return render_template('tool.html', tool=tool, accept_types=accept_types)
