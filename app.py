import subprocess
import sys

# Installer les packages nécessaires
def install_packages():
    subprocess.check_call([sys.executable, "-m", "pip", "install", "folium"])
    subprocess.check_call([sys.executable, "-m", "pip", "install", "streamlit-folium"])
    subprocess.check_call([sys.executable, "-m", "pip", "install", "streamlit"])

# Appeler la fonction pour installer les packages
install_packages()

# Vérification
import streamlit as st
import folium
from streamlit_folium import st_folium
print("Les packages streamlit, folium et streamlit-folium sont installés et prêts à être utilisés !")

import json




# Charger les données utilisateur collectées
try:
    with open("user_data.json", "r") as json_file:
        user_data = json.load(json_file)
        print("Données utilisateur récupérées :", user_data)
except FileNotFoundError:
    print("Aucune donnée utilisateur n'a été collectée. Lancez 'questions.py' pour collecter les données.")




# On importe les festivals
import pandas as pd

# Charger df_end depuis le fichier CSV
df_end = pd.read_csv('df_end.csv')

# Fonction pour afficher les festivals sur la carte
def afficher_festivals_sur_carte(festivals, user_location):
    """
    Affiche les festivals sur une carte interactive avec l'adresse de l'utilisateur.
    
    Arguments :
    festivals -- DataFrame contenant les informations des festivals
    Chaque festival doit avoir les colonnes : 
    'Nom du festival', 'Géocodage xy', 'Période principale de déroulement du festival',
    'Discipline dominante', 'Envergure territoriale', 'Site internet du festival'.
    user_location -- Tuple contenant (latitude, longitude) pour l'adresse de l'utilisateur
    """
    carte = folium.Map(location=user_location, zoom_start=6, tiles="OpenStreetMap")
    
    # Ajouter un marqueur pour l'utilisateur
    folium.Marker(
        location=user_location,
        popup=f"<b>Votre adresse</b>",
        tooltip="Votre position 📍",
        icon=folium.Icon(color='red', icon='info-sign')
    ).add_to(carte)
    
    # Ajouter un marqueur pour chaque festival
    for _, row in festivals.iterrows():
        # Extraire les coordonnées depuis la colonne 'Géocodage xy'
        try:
            lat, lon = map(float, row['Géocodage xy'].split(','))
        except (ValueError, AttributeError):
            continue  # Ignorer si les coordonnées ne sont pas valides
        
        nom = row['Nom du festival']
        date = row['Période principale de déroulement du festival']
        description = f"{row['Discipline dominante']} - {row['Envergure territoriale']}"
        lien = row['Site internet du festival'] if pd.notna(row['Site internet du festival']) else "#"
        
        # Ajouter un marqueur avec popup
        popup_content = f"""
        <b>{nom}</b><br>
        Date : {date}<br>
        {description}<br>
        <a href="{lien}" target="_blank" style="color:blue; text-decoration:underline;">Lien vers le site</a>
        """
        folium.Marker(
            location=[lat, lon],
            popup=popup_content,
            tooltip=nom,
            icon=folium.Icon(color='blue', icon='info-sign')
        ).add_to(carte)
    
    return carte


user_location = user_data['coordinates']

# Afficher la carte dans Streamlit
st.title("Carte des Festivals en France")
carte = afficher_festivals_sur_carte(df_end, user_location)

# Afficher la carte interactive avec Streamlit
map_result = st_folium(carte, width=800, height=600)

# Afficher les informations du festival sélectionné
if map_result and map_result['last_object_clicked']:
    lat = map_result['last_object_clicked']['lat']
    lon = map_result['last_object_clicked']['lng']
    
    # Rechercher le festival correspondant
    for festival in festivals:
        if festival['latitude'] == lat and festival['longitude'] == lon:
            st.subheader(f"Informations sur {festival['nom']}")
            st.write(f"**Date** : {festival['date']}")
            st.write(f"**Description** : {festival['description']}")
            st.write(f"[Site du festival]({festival['lien']})")
            break