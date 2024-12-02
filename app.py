import os
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
import sqlite3

app = Flask(__name__)

# Définir un dossier où les images seront stockées
app.config['UPLOAD_FOLDER'] = 'static/uploads/'  # Chemin pour les fichiers téléchargés
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
    if request.method == "POST":
        # Récupérer le numéro de commande depuis le formulaire
        numero_commande = request.form.get("numero_commande")
        photo = request.files.get("photo")

        photo_path = None  # Initialiser photo_path à None

        if photo and allowed_file(photo.filename):
            # Sécuriser le nom du fichier pour éviter les problèmes de sécurité
            filename = secure_filename(photo.filename)
            photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # Sauvegarder le fichier dans le dossier uploads
            photo.save(photo_path)

            # Mettre à jour la base de données avec le chemin de l'image
            conn = sqlite3.connect("construction.db")
            cursor = conn.cursor()
            cursor.execute("UPDATE Commandes SET photo = ? WHERE numero_commande = ?", (photo_path, numero_commande))
            conn.commit()
            conn.close()

        # Récupérer le prix et la photo de la commande
        price, photo_path = get_price_and_photo(numero_commande)

        if price is not None:
            # Si la commande est trouvée, afficher le prix et l'image
            return render_template("index.html", price=price, error=None, photo_path=photo_path)
        else:
            # Si la commande n'est pas trouvée
            return render_template("index.html", price=None, error="Commande non trouvée.", photo_path=None)

    return render_template("index.html", price=None, error=None, photo_path=None)

if __name__ == "__main__":
    app.run(debug=True)
