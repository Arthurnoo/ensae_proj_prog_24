import streamlit as st
import requests

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

st.title("Recherche d'adresse")
st.markdown("Commencez à taper votre adresse pour obtenir des suggestions.")

# --- Étape 1 : Saisie de l'adresse par l'utilisateur ---
user_input = st.text_input("Entrez votre adresse :")

# --- Étape 2 : Afficher les suggestions en fonction de la saisie ---
if user_input:
    suggestions = get_address_suggestions(user_input)
    if suggestions:
        # Utiliser un selectbox pour afficher les suggestions
        selected_address = st.selectbox("Suggestions d'adresses :", suggestions)
        st.success(f"Adresse sélectionnée : {selected_address}")
    else:
        st.info("Aucune adresse correspondante trouvée.")
else:
    st.info("Tapez pour voir les suggestions d'adresses.")

