import streamlit as st
import requests
from datetime import date

def get_address_suggestions(query):
    """
    Utilise l'API data.gouv.fr pour récupérer des suggestions d'adresses.
    https://adresse.data.gouv.fr/api-doc/adresse
    """
    url = 'https://api-adresse.data.gouv.fr/search/'
    params = {
        'q': query,
        'limit': 5,  # Limiter le nombre de suggestions
        'autocomplete': 1  # Activer l'autocomplétion
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        suggestions = [feature['properties']['label'] for feature in data['features']]
        return suggestions
    return []

# --- Titre principal ---
st.title("Recommandation de festivals")
st.markdown("Répondez aux questions pour trouver le festival parfait pour vous !")

# --- Étape 1 : Adresse ---
st.header("1. Votre adresse")
user_input = st.text_input("Entrez votre adresse :")
if user_input:
    suggestions = get_address_suggestions(user_input)
    if suggestions:
        selected_address = st.selectbox("Suggestions d'adresses :", suggestions)
        st.success(f"Adresse sélectionnée : {selected_address}")
    else:
        st.warning("Aucune suggestion trouvée.")

# --- Étape 2 : Distance maximale ---
st.header("2. Distance maximale")
distance = st.radio(
    "Quelle est la distance maximale que vous êtes prêt(e) à parcourir pour un festival ?",
    ["Moins de 50 km", "Moins de 100 km", "Moins de 200 km", "Plus de 200 km"]
)
st.success(f"Distance choisie : {distance}")

# --- Étape 3 : Types de festivals ---
st.header("3. Genres de festivals")
categories = [
    "Musique", "Spectacle vivant", "Cinéma et audiovisuel",
    "Arts visuels et arts numériques", "Livre et littérature"
]
selected_categories = st.multiselect(
    "Sélectionnez les types de festivals qui vous intéressent :", categories
)
if "Musique" in selected_categories:
    music_genres = st.multiselect(
        "Genres musicaux :", 
        ["Jazz", "Blues", "Électronique", "Pop, rock", "Classique", "Hip-hop", "Reggae"]
    )
if "Spectacle vivant" in selected_categories:
    spectacle_genres = st.multiselect(
        "Types de spectacles vivants :",
        ["Théâtre", "Danse", "Cirque", "Marionnettes", "Arts de la rue"]
    )

# --- Étape 4 : Disponibilités ---
st.header("4. Vos disponibilités")
calendar_dates = st.date_input(
    "Sélectionnez vos dates disponibles :", 
    value=[date.today()], 
    min_value=date.today()
)

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
