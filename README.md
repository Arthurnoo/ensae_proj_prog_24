# ensae_proj_prog_24
Done

Projet de programmation pour cours ensae 2024/2025 : python pour la data science. Projet collaboratif entre Déchelette Madeleine, Marsot Mila et Neau Arthur

Festiv'Match est une application interactive qui simplifie la recherche de festivals en France, en fonction des préférences uniques de chaque utilisateur. Que vous soyez passionné de musique, de cinéma ou d’art, Festiv'Match vous aide à découvrir des festivals adaptés à vos goûts. Grâce à un questionnaire intuitif et personnalisé, l'application analyse vos préférences pour vous proposer les événements les plus pertinents.

Voici comment cela fonctionne. Notre projet est divisé en 3 parties. 
Une première partie composée des codes suivants :
- Nettoyage_base_donnees.ipynb
- Stats_descriptives.ipynb

Une deuxième partie composée des codes suivants : 
- scrapping_50_festivals_plus
- fusion_des_données.ipynb
- 50_festivals_geolocalisés.csv
- festivals_fusionnes_complets.csv
- festivals_sans_match.csv
- Stats_impact_gros_fest.ipynb

Une troisième et dernière partie avec les codes suivants :
- Nettoyage_base_donnees.py
- questions.py
- user_data.json
- filtre_festivals.ipynb
- app.py


I. Première partie : Statistiques descriptives générales.
Dans cette partie, notre but est d'analyser notre base de données principale, déposée sur le S3. On utilise alors cette base, que l'on nettoie des données impertinentes (Nettoyage_base_donnees.ipynb). Ensuite les statistiques descriptives sont dans le code Stats_descriptives.ipynb.


II. Deuxième partie : Impact des gros festivals.
Une idée que nous avons eu est de regarder l'impact des gros festivals (en taille de recherche sur internet) sur les plus petits festivals. Nous avons alors scrappé les 50 plus gros festivals (scrapping_50_festivals_plus_consultés.ipynb), que nous mettons dans le fichier 50_festivals_geolocalises.csv. Nous faisons ensuite le lien entre ces 50 gros festivals et notre base de données (fusion_des_données.ipynb). Nous avons alors une nouvelle base des 50 gros festivals et leurs informations provenants de notre base de départ (festivals_fusionnes_complets.csv) et si nous ne trouvons pas de correspondance, alors nous les mettons dans festivals_sans_match.csv. 
Cela nous permet ensuite de faire des statistiques sur l'impact de ces 50 festivals sur tous les autres (Stats_impact_gros_fest.ipynb).

III. Troisième partie : Moteur de recherche.
Avant de faire fonctionner questions.py et app.py, il faut installer les modules suivants :
- pip install streamlit
- pip install geopy
- pip install folium
- pip install streamlit-folium

La base de notre projet était un moteur de recherche des festivals en fonction d'un questionnaire personnel (questions.py). Il suffit alors de le lancer (streamlit run questions.py) pour tomber sur un questionnaire (y répondre). Ensuite, nous cherchons des correspondances (filtre_festivals.ipynb) avec les festivals de notre base de données de départ, que nous affichons dans la carte finale (app.py). Nous transmettons les informations entre temps par user_data.json.

Pour faire tourner le questionnaire (questions.py : streamlit run questions.py)
