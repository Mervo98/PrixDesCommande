from flask import Flask, render_template_string, request
from werkzeug.utils import secure_filename
from pathlib import Path
import sqlite3

app = Flask(__name__)

# Définir un dossier où les images seront stockées
UPLOAD_FOLDER = Path("static/uploads/")  # Utiliser Path pour une gestion des chemins plus sûre
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)  # Créer le dossier s'il n'existe pas
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# Fonction pour vérifier si l'extension du fichier est valide
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Fonction pour récupérer le prix_total_apres_remise et l'image
def get_price_and_photo(numero_commande):
    try:
        # Connexion à la base de données
        conn = sqlite3.connect("construction.db")
        cursor = conn.cursor()
        
        # Requête pour récupérer le prix_total_apres_remise et la photo
        cursor.execute("SELECT prix_total_apres_remise, photo FROM Commandes WHERE numero_commande = ?", (numero_commande,))
        result = cursor.fetchone()
        
        # Fermer la connexion
        conn.close()
         
        if result:
            prix_total_apres_remise, photo_path = result
            return prix_total_apres_remise, photo_path  # Retourne le prix et le chemin de l'image
        else:
            return None, None  # Commande non trouvée
    except Exception as e:
        print("Erreur lors de la récupération des données :", e)
        return None, None

@app.route("/", methods=["GET", "POST"])
def index():
    # HTML sous forme de string
    index_html = """
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Recherche de Commande</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.1/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-5">
            <h1 class="text-center">Rechercher une Commande</h1>
            
            <!-- Formulaire pour rechercher une commande et télécharger une photo -->
            <form method="POST" action="/" enctype="multipart/form-data" class="mt-4">
                <div class="mb-3">
                    <label for="numero_commande" class="form-label">Numéro de Commande :</label>
                    <input type="text" id="numero_commande" name="numero_commande" class="form-control" placeholder="Entrez le numéro de commande" required>
                </div>
                
                <div class="mb-3">
                    <label for="photo" class="form-label">Téléchargez une Photo :</label>
                    <input type="file" id="photo" name="photo" class="form-control">
                </div>
                
                <button type="submit" class="btn btn-primary w-100">Rechercher</button>
            </form>
            
            <hr>

            <!-- Affichage du résultat -->
            {% if price is not none %}
                <div class="alert alert-success mt-4 text-center">
                    Prix Total Après Remise : <strong>{{ price }} €</strong>
                </div>
                {% if photo_path %}
                    <div class="text-center mt-4">
                        <img src="{{ url_for('static', filename='uploads/' + photo_path.split('/')[-1]) }}" alt="Photo de la commande" class="img-fluid rounded shadow">
                    </div>
                {% endif %}
            {% elif error %}
                <div class="alert alert-danger mt-4 text-center">
                    {{ error }}
                </div>
            {% endif %}
        </div>

        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.1/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """
    
    if request.method == "POST":
        numero_commande = request.form.get("numero_commande")
        photo = request.files.get("photo")

        photo_path = None  # Initialiser photo_path à None

        if photo and allowed_file(photo.filename):
            try:
                # Sécuriser le nom du fichier
                filename = secure_filename(photo.filename)
                photo_path = app.config['UPLOAD_FOLDER'] / filename
                
                # Sauvegarder le fichier dans le dossier uploads
                photo.save(photo_path)

                # Mettre à jour la base de données avec le chemin de l'image
                conn = sqlite3.connect("construction.db")
                cursor = conn.cursor()
                cursor.execute("UPDATE Commandes SET photo = ? WHERE numero_commande = ?", (str(photo_path), numero_commande))
                conn.commit()
                conn.close()
            except Exception as e:
                print("Erreur lors de l'enregistrement de la photo :", e)
                return render_template_string(index_html, price=None, error="Erreur lors de l'enregistrement de la photo.", photo_path=None)

        # Récupérer le prix et la photo de la commande
        price, photo_path = get_price_and_photo(numero_commande)

        if price is not None:
            return render_template_string(index_html, price=price, error=None, photo_path=photo_path)
        else:
            return render_template_string(index_html, price=None, error="Commande non trouvée.", photo_path=None)

    return render_template_string(index_html, price=None, error=None, photo_path=None)

if __name__ == "__main__":
    app.run(debug=True)
