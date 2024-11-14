import streamlit as st
import folium
from streamlit_folium import st_folium

# Fonction pour afficher les festivals sur la carte
def afficher_festivals_sur_carte(festivals, user_location):
    """
    Affiche les festivals sur une carte interactive avec l'adresse de l'utilisateur.
    
    Arguments :
    festivals -- Liste de dictionnaires contenant les informations des festivals
    Chaque festival doit avoir : 'nom', 'latitude', 'longitude', 'date', 'description', 'lien'
    user_location -- Tuple contenant (latitude, longitude) pour l'adresse de l'utilisateur
    """
    carte = folium.Map(location=[46.603354, 1.888334], zoom_start=5, tiles="OpenStreetMap")
    
    # Ajouter un marqueur pour l'utilisateur
    folium.Marker(
        location=user_location,
        popup=f"<b>Votre adresse</b>",
        tooltip="Votre position 📍",
        icon=folium.Icon(color='red', icon='info-sign')
    ).add_to(carte)
    
    # Ajouter un marqueur pour chaque festival
    for festival in festivals:
        nom = festival['nom']
        latitude = festival['latitude']
        longitude = festival['longitude']
        date = festival['date']
        description = festival['description']
        lien = festival['lien']
        
        # Ajouter un marqueur avec popup
        popup_content = f"""
        <b>{nom}</b><br>
        Date : {date}<br>
        {description}<br>
        <a href="{lien}" target="_blank" style="color:blue; text-decoration:underline;">Lien vers le site</a>
        """
        folium.Marker(
            location=[latitude, longitude],
            popup=popup_content,
            tooltip=nom,
            icon=folium.Icon(color='blue', icon='info-sign')
        ).add_to(carte)
    
    return carte

# Exemple d'utilisation
festivals = [
    {
        'nom': 'Festival de Cannes',
        'latitude': 43.5513,
        'longitude': 7.0128,
        'date': 'Mai 2024',
        'description': 'Festival international du film à Cannes.',
        'lien': 'https://www.festival-cannes.com/'
    },
    {
        'nom': 'Hellfest',
        'latitude': 47.126,
        'longitude': -1.254,
        'date': 'Juin 2024',
        'description': 'Festival de musique rock et métal à Clisson.',
        'lien': 'https://www.hellfest.fr/'
    },
    {
        'nom': 'Vieilles Charrues',
        'latitude': 48.275,
        'longitude': -3.564,
        'date': 'Juillet 2024',
        'description': 'Festival de musique à Carhaix.',
        'lien': 'https://www.vieillescharrues.asso.fr/'
    }
]

user_location = (48.8566, 2.3522)  # Paris

# Afficher la carte dans Streamlit
st.title("Carte des Festivals en France")
carte = afficher_festivals_sur_carte(festivals, user_location)

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
