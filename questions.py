import subprocess
import sys
import streamlit as st
import pandas as pd
import requests
from geopy.distance import geodesic
from datetime import date
import json

# --- Fonction : Installer les packages nécessaires ---
def install_packages():
    packages = ["streamlit", "pandas", "requests", "geopy"]
    for package in packages:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

install_packages()

# --- Fonction : Récupération des suggestions d'adresses ---
def get_address_suggestions(query):
    url = 'https://api-adresse.data.gouv.fr/search/'
    params = {'q': query, 'limit': 1}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        features = response.json().get('features', [])
        if features:
            coords = features[0]['geometry']['coordinates']
            address_text = features[0]['properties']['label']
            return (float(coords[1]), float(coords[0])), address_text
    return None, None

# --- Fonction principale ---
def collect_user_data():
    st.title("Recommandation de Festivals")
    st.markdown("Répondez aux questions pour trouver le festival parfait pour vous !")

    # --- Étape 1 : Informations personnelles ---
    st.header("1. Vos informations personnelles")
    user_name = st.text_input("Entrez votre nom :")
    user_email = st.text_input("Entrez votre email :")

    # --- Étape 2 : Adresse ---
    st.header("2. Votre adresse")
    user_address = st.text_input("Entrez votre adresse :")
    user_coords, user_address_text = None, None
    if user_address:
        user_coords, user_address_text = get_address_suggestions(user_address)
        if user_coords:
            st.success(f"Adresse trouvée : {user_address_text}")
        else:
            st.warning("Adresse introuvable. Veuillez vérifier votre saisie.")

    # --- Étape 3 : Distance maximale ---
    st.header("3. Distance maximale")
    user_distance_max = st.slider("Quelle distance maximale êtes-vous prêt(e) à parcourir ? (en km)", 0, 500, 100)

    # --- Étape 4 : Types et genres de festivals ---
    st.header("3. Vos préférences")
    user_types = st.multiselect("Types de festivals :", ["Musique", "Spectacle vivant", "Cinéma et audiovisuel", "Arts visuels et numériques", "Livre et littérature"])
    user_genres_musique = []
    user_genres_spectacle_vivant = []
    user_genres_cinema = []
    user_genres_arts_visuels = []
    user_genres_livre = []
    if "Musique" in user_types:
        user_genres_musique += st.multiselect("Genres musicaux :", ["Musique classique et opéra", "Musiques actuelles et populaires", "Musiques du monde", "Jazz, blues, RnB", "Musique rock et métal", "Musique instrumentale", "Musique et festivals thématiques", "Musiques électroniques", "Musique pour jeunes publics", "Musiques folk et patrimoniales"])
    if "Spectacle vivant" in user_types:
        user_genres_spectacle_vivant += st.multiselect("Genres de spectacle vivant :", ["Théâtre", "Danse", "Arts de la Rue", "Cirque", "Musique et Chant", "Marionnettes et Théâtre d'objets", "Spectacles pour Jeune Public", "Performance et Arts Visuels", "Humour et Café-Théâtre", "Pluridisciplinaire"])
    if "Cinéma et audiovisuel" in user_types:
        user_genres_cinema += st.multiselect("Genres de cinéma :", ["Cinéma généraliste long métrage", "Cinéma généraliste court métrage", "Audiovisuel et médias", "Festivals thématiques", "Cinématographies du monde", "Rétrospectives et classiques", "Techniques et métiers", "Cinéma et musique", "Cinéma expérimental et arts associés", "Jeunes publics", "Événements et projections spéciales"])
    if "Arts visuels et numériques" in user_types:
        user_genres_arts_visuels += st.multiselect("Genres d'arts visuels :", ["Arts numériques et vidéo", "Arts plastiques et visuels", "Design et architecture", "Arts urbains", "Performance et multimédia", "Littérature et illustration", "Photographie, cinéma et audiovisuel", "Art d’idées et sciences", "Autres"])
    if "Livre et littérature" in user_types:
        user_genres_livre += st.multiselect("Genres de littérature :", ["Romans et Littérature Générale", "Bandes Dessinées et Illustrations", "Jeunesse et Jeune Public", "Policier et Thriller", "Science-Fiction et Fantasy", "Littératures régionales et du Monde", "Édition et Métiers du Livre", "Conférences et Rencontres Littéraires", "Histoire et Patrimoine Littéraire", "Pluridisciplinaire : arts et littératures croisés "])

    # --- Étape 5 : Disponibilités ---
    st.header("5. Vos disponibilités")
    user_dates = st.date_input("Sélectionnez une période de disponibilité :", [date.today(), date.today()])

    # --- Étape 6 : Budget ---
    st.header("6. Votre budget")
    user_budget = st.slider("Budget pour le festival (en euros) :", 0, 500, (20, 100))

    # --- Étape 7 : Accessibilité ---
    st.header("7. Accessibilité")
    user_accessible = st.checkbox("Afficher uniquement les festivals accessibles aux personnes à mobilité réduite")

    # Stocker les données utilisateur
    user_data = {
        "name": user_name,
        "email": user_email,
        "address": user_address_text,
        "coordinates": user_coords,
        "distance_max": user_distance_max,
        "types": user_types,
        "genres musique": user_genres_musique,
        "genres spectacles vivants": user_genres_spectacle_vivant, 
        "genres cinéma et audiovisuel": user_genres_cinema,
        "genres arts visuels et numériques": user_genres_arts_visuels,
        "genres livre et littérature": user_genres_livre,
        "dates": [str(d) for d in user_dates],
        "budget": user_budget,
        "accessible": user_accessible
    }

    if st.button("Rechercher des festivals"):
        if not user_name or not user_email:
            st.error("Veuillez renseigner votre nom et votre email pour continuer.")
        else:
            st.success(f"Merci pour vos réponses, {user_name} ! Vos informations ont été enregistrées.")
            with open("user_data.json", "w") as json_file:
                json.dump(user_data, json_file)

if __name__ == "__main__":
    collect_user_data()