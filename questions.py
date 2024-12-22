# Ce code implémente une application interactive pour recommander des festivals en fonction des préférences des utilisateurs. 
# L'application utilise Streamlit pour l'interface utilisateur et l'API data.gouv.fr pour obtenir des suggestions d'adresses. 
# Les utilisateurs peuvent fournir leur adresse, définir une distance maximale, sélectionner des types de festivals et indiquer leurs disponibilités.

# Questionnaire : pour le lancer dans la page internet : écrire dans le terminal : streamlit run /home/onyxia/ensae_proj_prog_24/questions.py

import streamlit as st
import pandas as pd
import requests
from geopy.distance import geodesic
from datetime import date

# --- Fonction : Récupération des suggestions d'adresses via l'API data.gouv.fr ---
def get_address_suggestions(query):
    """
    Utilise l'API data.gouv.fr pour récupérer l'adresse en texte et ses coordonnées GPS.
    """
    url = 'https://api-adresse.data.gouv.fr/search/'
    params = {'q': query, 'limit': 1}  # Limiter à 1 résultat
    response = requests.get(url, params=params)
    if response.status_code == 200:
        features = response.json().get('features', [])
        if features:
            coords = features[0]['geometry']['coordinates']
            address_text = features[0]['properties']['label']
            return (float(coords[1]), float(coords[0])), address_text  # Retourne (latitude, longitude) et l'adresse en texte
    return None, None

# --- Fonction : Calcul de distance ---
def calculate_distance(coord1, coord2):
    """
    Vérifie que les coordonnées sont valides et calcule la distance.
    """
    if not (isinstance(coord1, tuple) and isinstance(coord2, tuple)):
        raise ValueError(f"Coordonnées invalides : {coord1}, {coord2}")
    if len(coord1) != 2 or len(coord2) != 2:
        raise ValueError(f"Les coordonnées doivent être des tuples (latitude, longitude)")
    return geodesic(coord1, coord2).kilometers

# --- Fonction : Filtrage des festivals ---
def filter_festivals(festivals, user_coords, user_distance_max, user_types, user_genres, user_dates, user_budget, user_accessible):
    filtered = []
    for _, row in festivals.iterrows():
        # Vérification de la distance
        festival_coords = (float(row['latitude']), float(row['longitude']))
        distance = calculate_distance(user_coords, festival_coords)
        if distance > user_distance_max:
            continue

        # Vérification du type de festival
        if row['type'] not in user_types:
            continue

        # Vérification du genre de festival
        if row['genre'] not in user_genres:
            continue

        # Vérification des dates
        festival_dates = pd.date_range(row['start_date'], row['end_date'])
        user_dates_range = pd.date_range(user_dates[0], user_dates[1])
        if not festival_dates.intersection(user_dates_range).any():
            continue

        # Vérification du budget
        if not (user_budget[0] <= row['budget_min'] <= user_budget[1] or user_budget[0] <= row['budget_max'] <= user_budget[1]):
            continue

        # Vérification de l'accessibilité
        if user_accessible and not row['accessible']:
            continue

        # Si toutes les conditions sont remplies, ajouter le festival
        filtered.append(row)

    return pd.DataFrame(filtered)

# --- Interface Streamlit ---
st.title("Recommandation de Festivals")
st.markdown("Répondez aux questions pour trouver le festival parfait pour vous !")

# --- Étape 1 : Adresse ---
st.header("1. Votre adresse")
user_address = st.text_input("Entrez votre adresse :")
user_coords = None
user_address_text = None

if user_address:
    user_coords, user_address_text = get_address_suggestions(user_address)
    if user_coords and user_address_text:
        st.success(f"Adresse trouvée : {user_address_text}")
    else:
        st.warning("Adresse introuvable. Veuillez vérifier votre saisie.")

# --- Étape 2 : Distance maximale ---
st.header("2. Distance maximale")
user_distance_max = st.slider("Quelle distance maximale êtes-vous prêt(e) à parcourir ? (en km)", 0, 500, 100)

# --- Étape 3 : Types et genres de festivals ---
st.header("3. Vos préférences")
user_types = st.multiselect("Types de festivals :", ["Musique", "Spectacle vivant", "Cinéma et audiovisuel", "Arts visuels et numériques", "Livre et littérature"])
user_genres = []
if "Musique" in user_types:
    user_genres += st.multiselect("Genres musicaux :", ["Jazz", "Blues", "Électronique", "Pop", "Classique", "Hip-hop", "Reggae"])
if "Spectacle vivant" in user_types:
    user_genres += st.multiselect("Genres de spectacle vivant :", ["Théâtre", "Danse", "Cirque", "Marionnettes", "Arts de la rue"])
if "Cinéma et audiovisuel" in user_types:
    user_genres += st.multiselect("Genres de cinéma :", ["Documentaire", "Fiction", "Animation", "Ciné-concert", "Court métrage"])

# --- Étape 4 : Disponibilités ---
st.header("4. Vos disponibilités")
user_dates = st.date_input("Sélectionnez une période de disponibilité :", [date.today(), date.today()])

# --- Étape 5 : Budget ---
st.header("5. Votre budget")
user_budget = st.slider("Budget pour le festival (en euros) :", 0, 500, (20, 100))

# --- Étape 6 : Accessibilité ---
st.header("6. Accessibilité")
user_accessible = st.checkbox("Afficher uniquement les festivals accessibles aux personnes à mobilité réduite")

# charger les données 
import pandas as pd
import streamlit as st

# --- Chargement des données ---
try:
    # Utilisez le chemin complet pour éviter les erreurs de répertoire
    festivals = pd.read_csv("/home/onyxia/ensae_proj_prog_24/festivals_en_France.csv")
    st.success("Données des festivals chargées avec succès.")
    st.write("Colonnes disponibles :", festivals.columns.tolist())  # Affiche les colonnes pour vérifier
    st.write("Aperçu des données :", festivals.head())  # Affiche les premières lignes pour valider
except FileNotFoundError:
    st.error("Le fichier 'festivals_en_France.csv' est introuvable. Vérifiez le chemin.")
    st.stop()
except pd.errors.EmptyDataError:
    st.error("Le fichier est vide. Assurez-vous qu'il contient des données.")
    st.stop()
except pd.errors.ParserError as e:
    st.error(f"Erreur de parsing du fichier CSV : {e}")
    st.stop()
except Exception as e:
    st.error(f"Une erreur inattendue est survenue : {e}")
    st.stop()
festivals = pd.read_csv("/home/onyxia/ensae_proj_prog_24/festivals_en_France.csv", sep=";")

import os
st.write("Répertoire actuel :", os.getcwd())  # Affiche le répertoire courant
st.write("Le fichier existe :", os.path.exists("/home/onyxia/ensae_proj_prog_24/festivals_en_France.csv"))

# Questionnaire : pour le lancer dans la page internet : écrire dans le terminal : streamlit run /home/onyxia/ensae_proj_prog_24/questions.py

import streamlit as st
import pandas as pd
import requests
from geopy.distance import geodesic
from datetime import date

# --- Fonction : Récupération des suggestions d'adresses via l'API data.gouv.fr ---
def get_address_suggestions(query):
    """
    Utilise l'API data.gouv.fr pour récupérer l'adresse en texte et ses coordonnées GPS.
    """
    url = 'https://api-adresse.data.gouv.fr/search/'
    params = {'q': query, 'limit': 1}  # Limiter à 1 résultat
    response = requests.get(url, params=params)
    if response.status_code == 200:
        features = response.json().get('features', [])
        if features:
            coords = features[0]['geometry']['coordinates']
            address_text = features[0]['properties']['label']
            return (float(coords[1]), float(coords[0])), address_text  # Retourne (latitude, longitude) et l'adresse en texte
    return None, None

# --- Fonction : Calcul de distance ---
def calculate_distance(coord1, coord2):
    """
    Vérifie que les coordonnées sont valides et calcule la distance.
    """
    if not (isinstance(coord1, tuple) and isinstance(coord2, tuple)):
        raise ValueError(f"Coordonnées invalides : {coord1}, {coord2}")
    if len(coord1) != 2 or len(coord2) != 2:
        raise ValueError(f"Les coordonnées doivent être des tuples (latitude, longitude)")
    return geodesic(coord1, coord2).kilometers

# --- Fonction : Filtrage des festivals ---
def filter_festivals(festivals, user_coords, user_distance_max, user_types, user_genres, user_dates, user_budget, user_accessible):
    filtered = []
    for _, row in festivals.iterrows():
        # Vérification de la distance
        festival_coords = (float(row['latitude']), float(row['longitude']))
        distance = calculate_distance(user_coords, festival_coords)
        if distance > user_distance_max:
            continue

        # Vérification du type de festival
        if row['type'] not in user_types:
            continue

        # Vérification du genre de festival
        if row['genre'] not in user_genres:
            continue

        # Vérification des dates
        festival_dates = pd.date_range(row['start_date'], row['end_date'])
        user_dates_range = pd.date_range(user_dates[0], user_dates[1])
        if not festival_dates.intersection(user_dates_range).any():
            continue

        # Vérification du budget
        if not (user_budget[0] <= row['budget_min'] <= user_budget[1] or user_budget[0] <= row['budget_max'] <= user_budget[1]):
            continue

        # Vérification de l'accessibilité
        if user_accessible and not row['accessible']:
            continue

        # Si toutes les conditions sont remplies, ajouter le festival
        filtered.append(row)

    return pd.DataFrame(filtered)



# --- Interface Streamlit ---
st.title("Recommandation de Festivals")
st.markdown("Répondez aux questions pour trouver le festival parfait pour vous !")

# --- Étape 1 : Informations utilisateur ---
st.header("1. Vos informations personnelles")
user_name = st.text_input("Entrez votre nom :")
user_email = st.text_input("Entrez votre email :")

# Vérification des informations personnelles
if user_name and user_email:
    st.success(f"Bienvenue, {user_name} ! Vos informations ont été enregistrées.")

# --- Étape 2 : Adresse ---
st.header("2. Votre adresse")
user_address = st.text_input("Entrez votre adresse :")
user_coords = None
user_address_text = None

if user_address:
    user_coords, user_address_text = get_address_suggestions(user_address)
    if user_coords and user_address_text:
        st.success(f"Adresse trouvée : {user_address_text}")
    else:
        st.warning("Adresse introuvable. Veuillez vérifier votre saisie.")

# --- Étape 3 : Distance maximale ---
st.header("3. Distance maximale")
user_distance_max = st.slider("Quelle distance maximale êtes-vous prêt(e) à parcourir ? (en km)", 0, 500, 100)

# --- Étape 4 : Types et genres de festivals ---
st.header("4. Vos préférences")
user_types = st.multiselect("Types de festivals :", ["Musique", "Spectacle vivant", "Cinéma et audiovisuel", "Arts visuels et numériques", "Livre et littérature"])
user_genres = []
if "Musique" in user_types:
    user_genres += st.multiselect("Genres musicaux :", ["Jazz", "Blues", "Électronique", "Pop", "Classique", "Hip-hop", "Reggae"])
if "Spectacle vivant" in user_types:
    user_genres += st.multiselect("Genres de spectacle vivant :", ["Théâtre", "Danse", "Cirque", "Marionnettes", "Arts de la rue"])
if "Cinéma et audiovisuel" in user_types:
    user_genres += st.multiselect("Genres de cinéma :", ["Documentaire", "Fiction", "Animation", "Ciné-concert", "Court métrage"])

# --- Étape 5 : Disponibilités ---
st.header("5. Vos disponibilités")
user_dates = st.date_input("Sélectionnez une période de disponibilité :", [date.today(), date.today()])

# --- Étape 6 : Budget ---
st.header("6. Votre budget")
user_budget = st.slider("Budget pour le festival (en euros) :", 0, 500, (20, 100))

# --- Étape 7 : Accessibilité ---
st.header("7. Accessibilité")
user_accessible = st.checkbox("Afficher uniquement les festivals accessibles aux personnes à mobilité réduite")

# --- Étape 8 : Stockage des réponses utilisateur ---
user_data = {
    "name": user_name,
    "email": user_email,
    "address": user_address_text,
    "coordinates": user_coords,
    "distance_max": user_distance_max,
    "types": user_types,
    "genres": user_genres,
    "dates": user_dates,
    "budget": user_budget,
    "accessible": user_accessible
}


if st.button("Rechercher des festivals"):
    if not user_name or not user_email:
        st.error("Veuillez renseigner votre nom et votre email pour continuer.")
    else:
        # Exemple de recherche fictive (vous pouvez ajouter votre filtre ici)
        # filtered_festivals = filter_festivals(...)
        st.success(f"Merci pour vos réponses, {user_name} ! Nous allons rechercher un festival qui correspond à vos préférences.")

# --- Résultats ---
st.header("Résultats")
if st.button("Trouver un festival"):
    # Exemple de résultat basé sur les réponses (à adapter avec un vrai algorithme)
    st.success("Nous avons trouvé un festival qui correspond à vos préférences ! 🎉")
    st.markdown(f"""
        **Adresse** : {selected_address if user_input else "Non spécifiée"}  
        **Distance maximale** : {distance}  
        **Catégories sélectionnées** : {', '.join(selected_categories) if selected_categories else "Aucune"}  
        **Disponibilités** : {', '.join([str(d) for d in calendar_dates]) if calendar_dates else "Non spécifiées"}
    """)

