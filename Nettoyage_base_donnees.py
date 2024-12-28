#!/usr/bin/env python
# coding: utf-8

# 
# 
# # Nettoyage de la base de données
# 
# ### <u>1. Description de la base de données
# 
# **Les données** </u>
# 
# La base de données utilisée est celle de Data.gouv qui liste les festivals en France. Les critères de sélection des festivals sont les suivants :
# - avoir eu lieu en 2019
# - avoir connu au moins deux éditions en 2019
# - se dérouler sur plus d’une journée
# - compter au moins 5 spectacles, représentations, concerts ou projections
# <u> 
# 
# 
# 
# **Description de la base de données** </u>
# 
# La base de donnée regroupe les éléments suivants :
# - Identité du festival : nom, disciplines dominantes, sous-catégorie au sein des disciplines
# - Données géographiques : région de déroulement, département, adresse postale, géocodage xy (coordonnées)
# - Données administratives : identifiant, code insee...
# - Données temporelles : période de déroulement, date de création...
# - Trouver/communiquer avec le festival : site internet et adresse mail.

# ### <u>2. Suppression des données inutiles 
# </u>
# 
# On a choisit de supprimer les colonnes suivantes : 
# - Code postal (de la commune principale de déroulement)
# - Code Insee commune
# - Code Insee EPCI
# - Libellé EPCI	
# - Numéro de voie	 
# - Type de voie (rue, Avenue, boulevard, etc.)	
# - Nom de la voie	
# - Adresse postale	
# - Complément d'adresse (facultatif)
# - Décennie de création du festival
# - Année de création du festival
# - Identifiant Agence A
# - identifiant CNM
# 
# On a aussi fait le choix de ne conserver que les festivals se déroulant en France métropolitaine. 
# 

# In[28]:


import s3fs
import pandas as pd

# Configuration du bucket et du chemin du fichier
MY_BUCKET = "arthurneau"  # Remplace par le nom de ton bucket
FILE_PATH_S3 = f"{MY_BUCKET}/diffusion/festivals_en_France (1).csv"  # Chemin complet sur MinIO

# Initialisation de la connexion à MinIO
fs = s3fs.S3FileSystem(client_kwargs={"endpoint_url": "https://minio.lab.sspcloud.fr"})

# Importer le fichier CSV depuis MinIO
with fs.open(FILE_PATH_S3, "r") as file_in:
    df = pd.read_csv(file_in, sep=';', encoding='utf-8-sig')

# Afficher les premières lignes
print(df.head())  # Afficher les 5 premières lignes

# Supprimer les colonnes qui ne nous intéressent pas
df = df.drop(["Code postal (de la commune principale de déroulement)", "Code Insee commune", "Code Insee EPCI", "Libellé EPCI", "Numéro de voie", "Type de voie (rue, Avenue, boulevard, etc.)", "Nom de la voie", "Adresse postale", "Complément d'adresse (facultatif)", "Décennie de création du festival", "Année de création du festival", "Identifiant Agence A", "identifiant CNM"], axis=1)

# Afficher les colonnes restantes pour vérifier
print(df.columns.tolist())


# Supprimer les festivals hors France métropolitaine
regions_non_metropolitaines = ["Guadeloupe", "Martinique", "Guyane", "La Réunion", "Mayotte", "Polynésie française", "Saint-Pierre-et-Miquelon", "Saint-Barthélemy"]
df = df[~df["Région principale de déroulement"].isin(regions_non_metropolitaines)]

# Vérifier le contenu après suppression
print(df["Région principale de déroulement"].unique())


# ### <u>3. Modification et mise en forme des données  
# 
# **Transformation des données** </u>
# 
# Transformation des données sous forme de listes de listes. La première clef utilisée est nom du festival_identifiant car il y a des festivals ayant le même nom mais se déroulant sur des communes différentes. Ajouter l'identifiant permet d'avoir une clef unique. 
# 
# On veut quelque chose de cette forme : {"nom-festival_id" : {"nom-festival:..., "date":..., }}, {"nom-festival_id2" : {...} }, etc. 
# 
# 
# 
# 

# Il semble d'abord qu'il faille nettoyer la base de données, puisqu'il y a des caractères invisibles dans les noms des colonnes.

# In[29]:


# Nettoyer les noms des colonnes pour supprimer les caractères invisibles
df.columns = df.columns.str.replace(r'^\ufeff', '', regex=True).str.strip()

# Vérifier les nouvelles colonnes
print(df.columns)


# In[30]:


# Construire un dictionnaire où chaque clé principale est "Nom du festival_Identifiant"
dictionnaire = {}
for _, row in df.iterrows():
    # Utiliser la colonne "Identifiant" du DataFrame comme partie de la clé
    cle_principale = f"{row['Nom du festival']}_{row['Identifiant']}"
    
    # Ajouter un sous-dictionnaire contenant toutes les colonnes, sauf la colonne "Identifiant"
    dictionnaire[cle_principale] = row.drop("Identifiant").to_dict()

# Afficher un exemple
list(dictionnaire.items())[:5]  # Afficher les 5 premières entrées du dictionnaire pour vérifier


# <u>
# 
# **La catégorie "pluridisciplinaire"**  </u>
# 
# Il s'agit ici d'expliciter la catégorie "pluridisciplinaire". En effet, l'utilisateur va cocher le type de festival qu'il souhaite : il faut donc spécifier à quelles disciplines appartient le festival pour que celui-ci apparaisse lorsque l'utilisateur cochera. Ainsi, si la colonne "Sous-catégorie [...]" n'est pas vide, on renomme la colonne "Discipline dominante" avec le nom de la sous-catégorie.
# 
# **Par exemple** : le festival "Rêves d'enfants" est noté pluridisciplinaire et est un festival de littérature et de spectacle vivant. Il faut qu'il apparaisse lorsque l'utilisateur coche "Littérature" ou "Spectacle vivant". On renomme ainsi la colonne "Discipline dominante" "Livre, littérature et Spectacle vivant". 
# 
# 
# Il reste néanmoins 290 festivals marqués comme "pluridisciplinaire" mais sans sous-catégorie renseignée. Nous avons donc choisi de supprimer ces festivals pour deux raisons : 
# 1. Dans le questionnaire, l'utilisateur clique sur une catégorie de festival qu'il souhaite, si le festival n'en a pas il ne peut cliquer dessus. 
# 2. Il y a trop de festivals dans ce cas (290) pour pouvoir ajouter manuellement les catégories en question. 
# 
# **Par exemple**, le festival Printemps de paroles est noté pluridisciplinaire, mais avec aucune sous-catégorie associée.

# In[31]:


# Liste des colonnes sous-catégories que l'on analyse
colonnes_sous_categories = [
    "Sous-catégorie spectacle vivant",
    "Sous-catégorie musique",
    "Sous-catégorie cinéma et audiovisuel",
    "Sous-catégorie arts visuels et arts numériques",
    "Sous-catégorie livre et littérature"
]

# Dictionnaire pour associer les colonnes de sous-catégorie à leurs noms dans "Discipline dominante"
mapping_discipline = {
    "Sous-catégorie spectacle vivant": "Spectacle vivant",
    "Sous-catégorie musique": "Musique",
    "Sous-catégorie cinéma et audiovisuel": "Cinéma, audiovisuel",
    "Sous-catégorie arts visuels et arts numériques": "Arts visuels, arts numériques",
    "Sous-catégorie livre et littérature": "Livre, littérature"
}

# Fonction pour renommer la discipline dominante en respectant les correspondances spécifiques
def renommer_discipline(row):
    # Si "Discipline dominante" est pluridisciplinaire
    if row["Discipline dominante"] == "Pluridisciplinaire":
        # Liste des disciplines à partir des sous-catégories non vides
        sous_categories = [mapping_discipline[col] for col in colonnes_sous_categories if pd.notna(row[col])]
        # Si au moins une sous-catégorie est trouvée, les utiliser
        if sous_categories:
            return " ; ".join(sous_categories)
        else:
            return "A supprimer"
    # Sinon, garder la valeur d'origine
    return row["Discipline dominante"]

# Appliquer la fonction sur le DataFrame
df["Discipline dominante"] = df.apply(renommer_discipline, axis=1)

# Supprimer les festivals marqués "A supprimer"
df = df[df["Discipline dominante"] != "A supprimer"]

# Vérifier les résultats
print(df[["Nom du festival", "Discipline dominante"]].head(50))


# <u>
# 
# **Modification des sous-catégories** </u>
# 
# Pour plus de clarté, nous avons choisis de modifier les sous-catégories présentes dans la base de données qui étaient beaucoup trop nombreuses et les avons réduits à 10 par catégorie. 

# **La catégorie Spectacle vivant :**

# In[32]:


import re  # Importer le module pour gérer les séparateurs multiples

# Dictionnaire élargi

regroupements_spectacle_vivant = {
    "Théâtre": [
        "Théâtre", "Théâtre - humour", "Théâtre ; Lecture publique", "Arts du théâtre",
        "Théâtre, Danse", "Théâtre, Marionnettes", "Théâtre, arts du conte",
        "Théâtre amateur", "Théâtre de rue", "Arts du théâtre théâtre d'humour",
        "Théâtre musical", "Théâtre - humour comédie", "Théâtre forain", "Du théâtre",
        "Contes", "Représentation", "Poésie", "Lecture…", "Arts du théâtre  théâtre d'humour",
        "Piano jazz théâtre"
    ],
    "Danse": [
        "Danse", "Danses traditionnelles", "Danse contemporaine", "Danse, théâtre",
        "Danses de rue", "Danse afro-contemporaine", "Danse de music’ hall",
        "Danse classique", "Danse theme monde arabe", "Danse theme  europe de l'est",
        "Danse et concerts tango", "Hip hop (danse)", "Capoeira", "Danse contemporaine et danse traditionnelle",
        "Danses", "Bal sévillan"
    ],
    "Arts de la Rue": [
        "Arts de la Rue", "Cirque et Arts de la rue", "Arts de la rue ; Théâtre",
        "Spectacles de rue", "Arts de la rue et Cirque", "Spectacle de rue",
        "Spectacle déambulatoire", "Spectacle de rues", "Arts de la rue et du cirque",
        "Street art", "Arts de la rue - concert - conte", "Des arts de la rue", "Rue",
        "Arts d la rue", "Cultures urbaines ", "Arts de la rue Musique", "Spectacles de rue concerts"
    ],
    "Cirque": [
        "Arts de la piste", "Nouveau Cirque", "Arts du cirque", "Cirque",
        "Clown", "Pyrotechnie", "Magie nouvelle", "Cirque traditionnel", "Mime", "Du cirque",
        "Spectacles équestres", "Arts du crique", " arts du clown"
    ],
    "Musique et Chant": [
        "Musique", "Musiques traditionnelles", "Chanson", "Concerts", "Opéra",
        "Musiques", "Musique ancienne", "Musique médiévale", "Musique et lectures",
        "Chansons théâtrales", "Blues (rythm'n'blues)", "Comédie musicale",
        "Jazz et musiques improvisées", "Musique classique", "Musiques arméniennes",
        "Reggae", "Rock", "Variétés", "Flamenco (musique)", "Musiques du monde",
        "Musiques amplifiées ou électroniques", "Soul funk", "Concerts pop electro",
        "Du chant", "Lecture en musique", "Musiques actuelles", "Musiques traditionnelles de provence",
        " amérique d'avant guerre) des spectacles pour enfants", "Cinéma", "(jazz", " musique savante ",
        " musique savante ", " Chant", " Bal sévillan", "Concours de chants", "Stage musique danse",
        "Rencontres autour de la musique", " Chant", " musique savante ", "Art lyrique ", "Hip-hop ", "Rap", " hip-hop ", " hip-hop / rap"
    ],
    "Marionnettes et Théâtre d'objets": [
        "Théâtre d'objet", "Marionnettes", "Théâtre d'objets", "Marionnettes et Théâtre visuel",
        "Arts de la marionnette", "Marionnettes et théâtre d'objet", "Marionnettes et théâtre d'objets-théâtre d'ombres",
        "Marionnettes-théâtre d'objets-théâtre d'ombres", "Art du mime et du geste", "Marionettes",
        "Marionnettes et théâtre d’objet", "Marionnette", "Marionnettes et théâtre d'objets"
    ],
    "Spectacles pour Jeune Public": [
        "Conte", "Jeune Public", "Conte musical", "Arts du conte",
        "Spectacle pour enfants", "Théâtre jeune public", "Concours de poésie",
        "Découverte des Amériques pour enfants", "Lecture publique", "De la poésie", " decouverte des ameriques pour enfants"
    ],
    "Performance et Arts Visuels": [
        "Performance", "Arts visuels", "photo", "vidéo", "Exposition",
        "Cinéma et audiovisuel", "Magie", "Sculptures", "Parité homme-femme",
        "Pyrotechnie", "Rencontres voyageurs", "Audiovisuel-cinéma", "Ciné-concert",
        "Lecture publique", "Découverte du patrimoine de l’Occitanie autrement",
        "Découverte du Japon", "Culture asiatique", "Thème culture franco colombienne", "theme culture franco colombienne", "La création artistique",
        "L´innovation technologique", "Le recyclage des matériaux", "Le partage des compétences techniques et artistiques",
        "Performance - installation", "Arts", "Rencontrer sur le theme de l'usage du faux et démocratie"
    ],
    "Humour et Café-Théâtre": [
        "Humour", "Théâtre d'humour/café-théâtre", "Café-Théâtre",
        "Théâtre d'humour", "Rires et saveurs: soirée dégustation et concert d'exception", " arts du clown"
    ],
    "Pluridisciplinaire": [
        "Pluridisciplinaire", "Pluridisciplinaire culture", "Pluridisciplinaire à dominante spectacle vivant",
        "Spectacle vivant pluridisciplinaire", "SV hors MUA", "Spectacle vivant",
        "Dégustation de vin", "Thème du Moyen Âge", "Découverte des Amériques pour enfants",
        "Terroir", "Performances", "Toutes les disciplines du spectacle vivant",
        "Conférence", "Solidarités", "Approche de la langue et la culture occitane",
        "Ateliers ouvertures vers l'autres", "Animaux", "Thème du voyage", "Sur le thème du voyage", "Theme du voyage et les sciences",
        "Theme amerique", "Le partage des compétences techniques et artistiques et les Droits Culturels dans le contexte géopolitique transfrontalier suivant les méthodologies de l´Écologie Acoustique.","Marché producteur locaux",
        "Découvrir le patrimoine de l’Occitanie autrement", "Autres (voix d'enfants)", "Animations", "Spectacles", "Et autres…",
        "Des bonnes tablées", "Representation", "Cultures urbaines ", "Bodégas", "Cultures urbaines ", " "
    ]
}

# Inverser le dictionnaire pour une recherche efficace
inverse_regroupements = {}
for categorie, sous_cats in regroupements_spectacle_vivant.items():
    for sous_cat in sous_cats:
        inverse_regroupements[sous_cat.lower().strip()] = categorie

# Fonction pour attribuer les sous-catégories
def attribuer_sous_categories(row):
    if "Spectacle vivant" not in str(row.get("Discipline dominante", "")):
        return None  # Si ce n'est pas du spectacle vivant, ne rien faire
    
    sous_categorie = row.get("Sous-catégorie spectacle vivant")
    if pd.isna(sous_categorie):  # Si la sous-catégorie est NaN
        return None
    
    sous_categories = re.split(r"[;,]", str(sous_categorie))  # Diviser en cas de multiples sous-catégories
    nouvelles_categories = set()
    for sous_cat in sous_categories:
        sous_cat_normalise = sous_cat.lower().strip()  # Normaliser : minuscule et sans espaces
        if sous_cat_normalise in inverse_regroupements:
            nouvelles_categories.add(inverse_regroupements[sous_cat_normalise])
        else:
            # Débogage pour les sous-catégories non reconnues
            print(f"Sous-catégorie non reconnue : '{sous_cat}' pour le festival '{row['Nom du festival']}'")
    return list(nouvelles_categories) if nouvelles_categories else None

# Appliquer la fonction uniquement si Discipline dominante contient "Spectacle vivant"
df["Nouvelles sous-catégories spectacle vivant"] = df.apply(attribuer_sous_categories, axis=1)



# In[33]:


##                  VÉRIFICATION DES RÉSULTATS 

# Filtrer les lignes où "Discipline dominante" contient "Spectacle vivant"
spectacle_vivant_df = df[df["Discipline dominante"].str.contains("Spectacle vivant", na=False)]
    
# Afficher uniquement les colonnes demandées pour les 250 premières lignes
print(spectacle_vivant_df[["Nom du festival", "Région principale de déroulement", "Discipline dominante", "Nouvelles sous-catégories spectacle vivant"]].head(50))


# In[34]:


# Suppression des festivals pour lesquels aucune sous-catégorie n'est renseignée. - il y en a environ 300 sur les 1600 festivals de Spectacle vivant. 

# Filtrer pour conserver uniquement les festivals pour lesquels la discipline dominante contient "Spectacle vivant"
#df = df[
   # ~(
#        df["Discipline dominante"].str.contains("Spectacle vivant", na=False) &  
#        (df["Nouvelles sous-catégories spectacle vivant"].isna() |  # La sous-catégorie est NaN
#         (df["Nouvelles sous-catégories spectacle vivant"] == "None"))  # La sous-catégorie est "None"
#    )
#]

##                  VÉRIFICATION DES RÉSULTATS 

# Afficher les résultats pour vérification
#print(df[["Nom du festival", "Sous-catégorie spectacle vivant", "Nouvelles sous-catégories spectacle vivant"]].head(20))

# Filtrer les lignes où "Discipline dominante" contient "Spectacle vivant"
#spectacle_vivant_df = df[df["Discipline dominante"].str.contains("Spectacle vivant", na=False)]
#print(spectacle_vivant_df[["Nom du festival", "Discipline dominante", "Nouvelles sous-catégories spectacle vivant"]].head(50))


# Pour faciliter le travail et avoir une idée de la taille des données traitées, on compte ici : 
# * Le nombre de festivals ayant pour discipline dominante "Spectacle vivant". 
# * Le nombre de festivals dans chaque sous-catégorie. 
# 

# In[35]:


# Compter les lignes où la colonne "Discipline dominante" contient "spectacle vivant"
count_spectacle_vivant = df["Discipline dominante"].str.contains("spectacle vivant", case=False, na=False).sum()

# Afficher le résultat
print(f"Nombre total de festivals ayant pour discipline dominante 'Spectacle vivant' : {count_spectacle_vivant}")


        # THÉÂTRE

# Compter les lignes où la sous-catégorie associée contient "Théâtre"
count_théâtre = df["Nouvelles sous-catégories spectacle vivant"].apply(
    lambda x: "Théâtre" in x if isinstance(x, list) else False
).sum()

# Afficher le résultat
print(f"Nombre total de festivals ayant pour sous-catégorie 'Théâtre' : {count_théâtre}")


        # DANSE

# Compter les lignes où la sous-catégorie associée contient "Danse"
count_danse = df["Nouvelles sous-catégories spectacle vivant"].apply(
    lambda x: "Danse" in x if isinstance(x, list) else False
).sum()

# Afficher le résultat
print(f"Nombre total de festivals ayant pour sous-catégorie 'Danse' : {count_danse}")


        # ARTS DE LA RUE 

# Compter les lignes où la sous-catégorie associée contient "Arts de la rue"
count_rue = df["Nouvelles sous-catégories spectacle vivant"].apply(
    lambda x: "Arts de la Rue" in x if isinstance(x, list) else False
).sum()

# Afficher le résultat
print(f"Nombre total de festivals ayant pour sous-catégorie 'Arts de la rue' : {count_rue}")


        # MUSIQUE ET CHANT 

# Compter les lignes où la sous-catégorie associée contient "Danse"
count_chant = df["Nouvelles sous-catégories spectacle vivant"].apply(
    lambda x: "Musique et Chant" in x if isinstance(x, list) else False
).sum()

# Afficher le résultat
print(f"Nombre total de festivals ayant pour sous-catégorie 'Musique et Chant' : {count_chant}")


        # CIRQUE

# Compter les lignes où la sous-catégorie associée contient "Cirque"
count_cirque = df["Nouvelles sous-catégories spectacle vivant"].apply(
    lambda x: "Cirque" in x if isinstance(x, list) else False
).sum()

# Afficher le résultat
print(f"Nombre total de festivals ayant pour sous-catégorie 'Cirque' : {count_cirque}")


        # MARIONNETTES ET THÉÂTRE D'OBJETS

# Compter les lignes où la sous-catégorie associée contient "Marionnettes et Théâtre d'objets"
count_marionnettes = df["Nouvelles sous-catégories spectacle vivant"].apply(
    lambda x: "Marionnettes et Théâtre d'objets" in x if isinstance(x, list) else False
).sum()

# Afficher le résultat
print(f"Nombre total de festivals ayant pour sous-catégorie 'Marionnettes et Théâtre d'objets' : {count_marionnettes}")
    

    # JEUNE PUBLIC

# Compter les lignes où la sous-catégorie associée contient "Spectacles pour Jeune Public"
count_jeune = df["Nouvelles sous-catégories spectacle vivant"].apply(
    lambda x: "Spectacles pour Jeune Public" in x if isinstance(x, list) else False
).sum()

# Afficher le résultat
print(f"Nombre total de festivals ayant pour sous-catégorie 'Spectacles pour Jeune Public' : {count_jeune}")


        # PERFORMANCE ET ARTS VISUELS

# Compter les lignes où la sous-catégorie associée contient "Performance et Arts Visuels"
count_visuels = df["Nouvelles sous-catégories spectacle vivant"].apply(
    lambda x: "Performance et Arts Visuels" in x if isinstance(x, list) else False
).sum()

# Afficher le résultat
print(f"Nombre total de festivals ayant pour sous-catégorie 'Performance et Arts Visuels' : {count_visuels}")

            
        # HUMOUR ET CAFÉ-THÉÂTRE 

# Compter les lignes où la sous-catégorie associée contient "Humour et Café-Théâtre"
count_humour = df["Nouvelles sous-catégories spectacle vivant"].apply(
    lambda x: "Humour et Café-Théâtre" in x if isinstance(x, list) else False
).sum()

# Afficher le résultat
print(f"Nombre total de festivals ayant pour sous-catégorie 'Humour et Café-Théâtre' : {count_humour}")


        # PLURIDISCIPLINAIRE 

# Compter les lignes où la sous-catégorie associée contient "Pluridisciplinaire"
count_pluri = df["Nouvelles sous-catégories spectacle vivant"].apply(
    lambda x: "Pluridisciplinaire" in x if isinstance(x, list) else False
).sum()

# Afficher le résultat
print(f"Nombre total de festivals ayant pour sous-catégorie 'Pluridisciplinaire' : {count_pluri}")


# **La catégorie Arts visuels, arts numériques :**

# In[36]:


# Problèmes dans les sorties "Sous catégorie non reconnue" à cause des virgules dans les parenthèses que le code prend pour un séparateur alors qu'il ne devrait pas. 

import re

def split_with_parentheses_handling(text):
    # Vérifier si le texte est valide
    if not isinstance(text, str) or not text.strip():
        return []
    
    # Diviser en utilisant la regex pour ignorer les virgules dans des parenthèses
    return re.split(r',\s*(?![^(]*\))', text.strip())


# In[37]:


import re

# Dictionnaire des regroupements pour Arts Visuels

regroupements_arts_visuels = {
    "Arts numériques et vidéo": [
        "Numérique", "Arts audiovisuels", "Vidéo", "Video : oeuvres multiples d'artistes",
         "Installation numérique", "Jeu vidéo", "Jeux vidéos", 
        "Arts visuels numériques", "Création sur internet", "Vulgarisation", "Formes immersives et interactives", "Art vidéo", "Vidéos d'artistes", "Oeuvres XR (réalité virtuelle et réalité augmentée)", "Arts numériques", "Arts visuels (arts multimédia) ; création contemporaine ; numérique"
    ],

    "Arts plastiques et visuels": [
        "Arts plastiques", "Art plastique", "Sculptures", "Sculpture", "Peinture", "Arts plastiques et visuels",
        "Expositions", "Arts visuels", "Gravure", "Gravures", "Estampes", "Dessin", "Graphisme",
        "Calligraphie et Patrimoine Ecrit", "Art contemporain en général (peinture",
        "Art contemporain au sens large", "Art contemporain et patrimoine", "Expositions d'art contemporain", "Exposition de clocher en clocher", "Art contemporain", "Arts graphiques", "Typographie", "Autres (estampe)", "Céramique", "Vitrail", "Création contemporaine", "Installations artistiques", "Exposition d'art contemporain dans des sites naturels", 
        "Art contemporain en général (peinture, sculpture,...)"
    ],
    
    "Design et architecture": [
        "Design", "Architecture", "Design graphique", "Paysagisme",
        "Mode et design", "Biennale d'architecture et d'urbanisme", 
        "Festival d'architecture", "Festival des Architectures vives", "Paris Design Week", "Festival international de design - design parade Hyères", "Design textile", "Autres : Design", "Autres (textile)", "Art textile",

    ],

    "Arts urbains": [
        "Arts urbains", "Street art", "Graff", 
        "Expériences urbaines", "Arts de la rue", "Graffiti", "Art dans l'espace public",
        "Art en plein air", "In situ", "Bien Urbain, art dans (et avec) l'espace public", "Arts visuel / Art dans l'espace public / Street Art", "Land art", "Parcours Land Art"
    ],

    "Performance et multimédia": [
        "Performance", "Performances", "Installation", "Installations", "Performances multimédias",
        "Ateliers avec les habitants de la ville", "Performances et spectacles hybrides contemporains entre corps et son",
        "Démonstrations", "Rencontres", "Animations diverses", "Performance costume", 
"Performance costume", "Performances multimédias", "Performance - installation", "danse", 'arts de la scène', "Art contemporain ; performance - installation"
    ],

    "Musique et arts sonores": [
        "Musique", "Art sonore et nouvelle musique", "Musiques actuelles",
        "Vinyls", "Nouvelle musique", "Jeune Création", "Street Music", "Arts visuels ; danse ; musique ; théâtre"
    ],

    "Littérature et illustration": [
        "Dessin de presse", "Bande dessinée", "Autre (Dessin)",
        "Calligraphie", "Livres d'artiste", "Salon d'éditions", "Colloque universitaire", "Illustration", "Éditions d'artiste", 'théâtre', 'Théâtre/ danse / musique'
    ],

    "Photographie, cinéma et audiovisuel": [
        "Audiovisuel", "Documentaire", "Vidéos d'artistes", "Programmations croisées avec le cinéma",
        "Cinéma", "Festival d'idées", "Expositions et projections photographie", "Programmations croisées avec le cinéma", "Cinéma et audiovisuel", "Projections documentaires", "Arts visuels (arts multimédia)", "Photographie", "Photo", "Photo exposition à ciel ouvert", "Exposition à ciel ouvert",
        "Photographies", "Street photography", "Vidéo mapping", "Micro édition", "Expositions de photographie", "Photo Montier", "Festival de Street Photography", "Autres (photographie)", 'photographie cinéma rencontres', "Arts visuels ; musiques actuelles ; photographie"
    ],

    "Art d’idées et sciences": [
        "Arts et sciences visionnaires", "Vulgarisation scientifique",
        "Festival d'idées", "Conférence table ronde thème environnement",
        "Festival artistique et citoyen qui questionne notre rapport à l’autre",
        "Sciences et arts", "Exploration des sciences dans les arts"
    ],

    "Autres": [
        "Spectacle vivant", "Culture juive", "Festival artistique et citoyen",
        "Autres : Performances", "Etc.", "Autres (artisans d'art)", "Multiples", "Métiers d'art", "Autres (artisans d'art)", "Autre : Métier d'art de la Céramique",
"Festival des métiers d'art",   "Divers", "Etc.", "Autres (voix d'enfants)", 
        "À l’accueil", "À l’étranger", "Au bien-vivre ensemble dans la diversité", "Pluridisciplinaire", "Autre : Performances"
    ]
}


# Inverser le dictionnaire pour recherche
inverse_regroupements_arts_visuels = {}
for categorie, sous_cats in regroupements_arts_visuels.items():
    for sous_cat in sous_cats:
        inverse_regroupements_arts_visuels[sous_cat.lower().strip()] = categorie

# Fonction pour attribuer les sous-catégories

def attribuer_sous_categories_arts_visuels(row):
    discipline_dominante = str(row.get("Discipline dominante", "")).strip().lower()  # Normalisation
    
    # Vérifier si la discipline dominante contient "arts visuels, arts numériques"
    if "arts visuels, arts numériques" not in discipline_dominante:
        return None

    sous_categorie = row.get("Sous-catégorie arts visuels et arts numériques")
    if pd.isna(sous_categorie):  # Si NaN, retourner None
        return None

    sous_categories = split_with_parentheses_handling(str(sous_categorie))  # Diviser en cas de multiples sous-catégories
    nouvelles_categories = set()
    for sous_cat in sous_categories:
        sous_cat_normalise = sous_cat.lower().strip()  # Normaliser
        if sous_cat_normalise in inverse_regroupements_arts_visuels:
            nouvelles_categories.add(inverse_regroupements_arts_visuels[sous_cat_normalise])
        else:
            # Afficher les sous-catégories non reconnues
            print(f"Sous-catégorie non reconnue : '{sous_cat.strip()}' pour le festival '{row['Nom du festival']}'")
    return list(nouvelles_categories) if nouvelles_categories else None

# Appliquer la fonction
df["Nouvelles sous-catégories arts visuels"] = df.apply(attribuer_sous_categories_arts_visuels, axis=1)



#ajouter base art à la main 


# In[38]:


##                  VÉRIFICATION DES RÉSULTATS 

# Filtrer les festivals pour lesquels la discipline dominante est "Arts visuels, Arts numériques"
arts_visuels_df = df[df["Discipline dominante"].str.contains("Arts visuels", na=False, case=False)]

# Afficher les premières lignes pour vérifier
print(arts_visuels_df[["Nom du festival", "Discipline dominante", "Nouvelles sous-catégories arts visuels"]].head(50))


# Pour faciliter le travail et avoir une idée de la taille des données traitées, on compte ici : 
# * Le nombre de festivals ayant pour discipline dominante "Arts visuels, arts numériques". 
# * Le nombre de festivals dans chaque sous-catégorie. 
# 

# In[39]:


# Compter les lignes où la colonne "Discipline dominante" contient "arts visuels, arts numériques"
count_arts_visuels = df[df["Discipline dominante"].str.contains("Arts visuels, arts numériques", case=False, na=False)].shape[0]

# Afficher le résultat
print(f"Nombre total de festivals avec 'arts visuels et arts numériques' : {count_arts_visuels}")


        # ARTS NUMÉRIQUES ET VIDÉO

# Compter les lignes où la sous-catégorie associée contient "Arts numériques et vidéo"
count_vidéo = df["Nouvelles sous-catégories arts visuels"].apply(
    lambda x: "Arts numériques et vidéo" in x if isinstance(x, list) else False
).sum()

# Afficher le résultat
print(f"Nombre total de festivals ayant pour sous-catégorie 'Arts numériques et vidéo' : {count_vidéo}")


        # ARTS PLASTIQUES ET VISUELS

# Compter les lignes où la sous-catégorie associée contient "Arts plastiques et visuels"
count_plastique = df["Nouvelles sous-catégories arts visuels"].apply(
    lambda x: "Arts plastiques et visuels" in x if isinstance(x, list) else False
).sum()

# Afficher le résultat
print(f"Nombre total de festivals ayant pour sous-catégorie 'Arts plastiques et visuels' : {count_plastique}")


        # DESIGN ET ARCHITECTURE

# Compter les lignes où la sous-catégorie associée contient "Design et architecture"
count_design = df["Nouvelles sous-catégories arts visuels"].apply(
    lambda x: "Design et architecture" in x if isinstance(x, list) else False
).sum()

# Afficher le résultat
print(f"Nombre total de festivals ayant pour sous-catégorie 'Design et architecture' : {count_design}")


        # ARTS URBAINS

# Compter les lignes où la sous-catégorie associée contient "Arts urbains"
count_urbains = df["Nouvelles sous-catégories arts visuels"].apply(
    lambda x: "Arts urbains" in x if isinstance(x, list) else False
).sum()

# Afficher le résultat
print(f"Nombre total de festivals ayant pour sous-catégorie 'Arts urbains' : {count_urbains}")


        # PERFORMANCE ET MULTIMÉDIAS

# Compter les lignes où la sous-catégorie associée contient "Performance et multimédia"
count_perf = df["Nouvelles sous-catégories arts visuels"].apply(
    lambda x: "Performance et multimédia" in x if isinstance(x, list) else False
).sum()

# Afficher le résultat
print(f"Nombre total de festivals ayant pour sous-catégorie 'Performance et multimédia' : {count_perf}")


        # MUSIQUE ET ART SONORE

# Compter les lignes où la sous-catégorie associée contient "Musique et arts sonores"
count_musique = df["Nouvelles sous-catégories arts visuels"].apply(
    lambda x: "Musique et arts sonores" in x if isinstance(x, list) else False
).sum()

# Afficher le résultat
print(f"Nombre total de festivals ayant pour sous-catégorie 'Musique et arts sonores' : {count_musique}")
    

        # PHOTOGRAPHIE, CINÉMA ET AUDIOVISUEL

# Compter les lignes où la sous-catégorie associée contient "Photographie, cinéma et audiovisuel"
count_photo = df["Nouvelles sous-catégories arts visuels"].apply(
    lambda x: "Photographie, cinéma et audiovisuel" in x if isinstance(x, list) else False
).sum()

# Afficher le résultat
print(f"Nombre total de festivals ayant pour sous-catégorie 'Photographie, cinéma et audiovisuel' : {count_photo}")


        # ART D'IDÉES ET SCIENCES

# Compter les lignes où la sous-catégorie associée contient "Art d’idées et sciences"
count_sciences = df["Nouvelles sous-catégories arts visuels"].apply(
    lambda x: "Art d’idées et sciences" in x if isinstance(x, list) else False
).sum()

# Afficher le résultat
print(f"Nombre total de festivals ayant pour sous-catégorie 'Art d’idées et sciences' : {count_sciences}")

            
        # LITTÉRATURE ET ILLUSTRATION

# Compter les lignes où la sous-catégorie associée contient "Littérature et illustration"
count_litt = df["Nouvelles sous-catégories arts visuels"].apply(
    lambda x: "Littérature et illustration" in x if isinstance(x, list) else False
).sum()

# Afficher le résultat
print(f"Nombre total de festivals ayant pour sous-catégorie 'Littérature et illustration' : {count_litt}")


        # AUTRES 

# Compter les lignes où la sous-catégorie associée contient "Autres"
count_autres = df["Nouvelles sous-catégories arts visuels"].apply(
    lambda x: "Autres" in x if isinstance(x, list) else False
).sum()

# Afficher le résultat
print(f"Nombre total de festivals ayant pour sous-catégorie 'Autres' : {count_autres}")


# **La catégorie Cinéma, audiovisuel :**

# In[40]:


# Problèmes dans les sorties "Sous catégorie non reconnue" à cause des virgules dans les parenthèses que le code prend pour un séparateur alors qu'il ne devrait pas. 

import re

def split_with_parentheses_handling(text):
    # Vérifier si le texte est valide
    if not isinstance(text, str) or not text.strip():
        return []
    
    # Diviser en utilisant la regex pour ignorer les virgules dans des parenthèses
    return re.split(r',\s*(?![^(]*\))', text.strip())


# In[41]:


import re

# Dictionnaire des regroupements pour Cinéma, audiovisuel

regroupements_cinema = {
    "Cinéma généraliste long métrage": [
        "Films", "Long métrages", "Documentaires", "Documentaire", "Cinéma d'auteur", "Fictions", "Ciné-concert", "Fiction long métrage", "Film documentaire", "Films de fiction longs métrages (plus d'une heure)",
        "Fiction longs métrages", "Cinéma", "Généraliste", "Films de comédie Longs métrages", "Longs métrages toutes disciplines",
        "Film grand public (fil conducteur la provence)", "Fiction long métrage / Documentaire", "Téléfilm", "cinema", "Fiction long métrage Court métrage Documentaire",
        "Audiovisuel-cinéma", "Fiction long-métrage", "Musique", "danse", "théâtre", "cinéma et audiovisuel", "monde entier fictions docu clips reportages animations films", "Arts visuels",
        "long métrage", "Longs métrages (Toutes disciplines)", "Non-fiction (documentaire autobiographie essai etc)"
    ],  

    "Cinéma généraliste court métrage": [
        "Court métrages", " Court métrage", "Courts-métrages", 
        "Compétition de courts-métrages", "Jeune public court métrage", "Court métrage francais et international", "court metrage long metrage",
        "Courts et longs métrages de fiction", "court metrage fantastique", "Court-métrage", 
        "Compétition de courts-métrages", "concours 48h", "Série courte de fiction & documentaire", "Court metrage par collgiens et lycéens", "Films documentaires courts et moyens métrages"
    ],

    "Audiovisuel et médias": [
        "Audiovisuel", "Télévision", "Webséries", "Contenus digitaux", "Streaming", "Vidéos du web", "Webseries", "Jeu vidéo", "web films ou productions télé", "Jeux vidéo", "Clip",
        "Arts numériques", "Vidéo"
    ],

    "Festivals thématiques": [
        "Cinéma de genre", "Cinéma d'horreur", "Cinéma fantastique", "Cinéma LGBTQ+",
        "Cinéma et environnement", "Cinéma et société", "Cinéma et patrimoine", "Drame", "Romance", "Festival consacré au film d'animation", "Fantastique", "SF", "épouvante", "Indépendant", "Documentaire politique", "Séries",
        "LGBTI (toutes disciplines)", "Films divers avec pour thématique l'homme et l'animal", "Festival du cinéma hédoniste", 
        "Toutes", "hybrides…", "cinema documentaire indépendant et engagé", "LGBTQIA+", "Film policier", "thème de l’alimentation UN ÉCO-FESTIVAL", "Films Aventure et Voyage"
    ],

    "Cinématographies du monde": [
        "Cinéma européen", "Cinéma asiatique", "Cinéma africain",
        "Cinéma américain", "Cinéma latino-américain", "Cinémas étrangers", "Cinéma britannique", 
        "Films en lien avec la région Occitanie", "Fiction long métrage / FESTIVAL DES CINEMAS HISPANO AMERICAIN", "cine suisse", 
        "Audiovisuel-cinéma ; culture asie-pacifique", "Audiovisuel-cinéma ; culture amériques-caraibes ; culture europe", 
        "Audiovisuel-cinéma ; culture asie-pacifique"
    ],

    "Rétrospectives et classiques": [
        "Cinéma classique", "Hommages", "Films restaurés",
        "Grands réalisateurs", "Cinéma des années 60", "Cinéma muet", "Rétrospective de carrière", 
        "Autrs : Films classiques",
        "films de patrimoine", "Compétition internationale de premières œuvres et rétrospectives",  "FILMS ESSAI", "film d'archives", "patrimoine"
    ],

    "Techniques et métiers": [
        "Montage", "Réalisation", "Effets spéciaux", "Scénarisation",
        "Photographie de cinéma", "Métiers du cinéma", "Casting", "Films d'ateliers", "Atelier de scénario", "Film en cours de fabrication", "Photographie documentaire", "Radio et création sonore",
        "Films d’étudiants", "d’ateliers et premières oeuvres auto-produites"
    ],

    "Cinéma et musique": [
        "Musique de film", "Comédies musicales", "Bande originale",
        "Ciné-opéra", "Ciné-musique", "Cinéma et musique en plein air", 
        "Ciné concerts", "Court métrage et musique", 
        "Autres : ciné-concert/ciné-mix/ciné-spectacle/ciné-bal", "Ciné-Concerts", "Audiovisuel-cinéma ; musique expérimentale", "musique et cinema en plein air",
        "Musiques du monde ; musique traditionnelle", "cine-concert"
    ],

    "Cinéma expérimental et arts associés": [
        "Cinéma expérimental", "Vidéos d'artistes", "Art vidéo",
        "Performances visuelles", "Cinéma immersif", "Installation vidéo", "Film expérimental", "Films d'écoles de cinéma", "Cinéma VR", 
        "Expérimental", "Expérimental /web/ photo", "Cinéma expérimental et image en mouvement", "arts numériques + VR", "film expérimental - ciné concert -", "Art vidéo et performance",
        "Film expérimental (court et long métrage)", "film d'artiste.", "cinéma documentaire indépendant et engagé", "Courts et longs métrages expérimentaux", "Séries; Expérimental..."
    ],  
        
    "Jeunes publics": [
        "Cinéma jeune public", "Films pour enfants", "Films d'animation", "Film d'animation", "Animation",
        "Ciné-contes", "Jeune public", "Films scolaires et universitaires", "Court metrage par collgiens et lycéens"
        "Principe d'éducation à l'image: des enfants apprennent à créer des films courts à destination d'autres enfants.", "Enfance et jeunesse", "Jeune public (CM, animation, fiction)", 
        "Ateliers pour enfants", "VR et jeune public", "Film scolaire et universitaire", "Film d'animatoin", "Principe d'éducation à l'image: des enfants apprennent à créer des films courts à destination d'autres enfants.",
        "Jeunes publics"
    ],

    "Événements et projections spéciales": [
        "cinéma et gastronomie", "Avant-premières", "Rencontres avec les réalisateurs", "Projections en plein air",
        "Tables rondes", "Ciné-débats", "Projections spéciales", "Fiction long métrage; Court métrage", "Films muets du patrimoine et piano", "Concours Films et Images sous-marines", "avants-premières uniquement","coups de coeur", 
        "Films libres de critique sociale", "Périples & cie", "cinema et spectacle", "VR", "Premiers films", "concours photo"
    ]
}


# Artdanthé : ajouté à la main, d'où présence de "Musique", "danse" et "théâtre" dans la catégorie 1. Sur son site internet, le festival présente bien une page cinéma. 
# Festival "Bleue" : à supprimer -> rien à voir avec le cinéma? 
# Sous-catégorie non reconnue : 'tous types de productions auivisuelles' pour le festival 'Festival Intergalactique de l'Image Alternative' -> ignorer 
# Ignorer Laterna magica dans la sortie "catégorie non reconnue" (déjà attribué à la bonne sous catégorie)
# Ignorer Sous-catégorie non reconnue : 'spectacle vivant' pour le festival 'Liberté + in&out toulon'


# Inverser le dictionnaire pour recherche
inverse_regroupements_cinema = {}
for categorie, sous_cats in regroupements_cinema.items():
    for sous_cat in sous_cats:
        inverse_regroupements_cinema[sous_cat.lower().strip()] = categorie

# Fonction pour attribuer les sous-catégories

def attribuer_sous_categories_cinema(row):
    discipline_dominante = str(row.get("Discipline dominante", "")).strip().lower()  # Normalisation
    
    # Vérifier si la discipline dominante contient "Cinéma, audiovisuel"
    if "audiovisuel" not in discipline_dominante:
        return None

    sous_categorie = row.get("Sous-catégorie cinéma et audiovisuel")
    if pd.isna(sous_categorie):  # Si NaN, retourner None
        return None

    sous_categories = split_with_parentheses_handling(str(sous_categorie))  # Diviser en cas de multiples sous-catégories
    nouvelles_categories = set()
    for sous_cat in sous_categories:
        sous_cat_normalise = sous_cat.lower().strip()  # Normaliser
        if sous_cat_normalise in inverse_regroupements_cinema:
            nouvelles_categories.add(inverse_regroupements_cinema[sous_cat_normalise])
        else:
            # Afficher les sous-catégories non reconnues
            print(f"Sous-catégorie non reconnue : '{sous_cat.strip()}' pour le festival '{row['Nom du festival']}'")
    return list(nouvelles_categories) if nouvelles_categories else None

# Appliquer la fonction
df["Nouvelles sous-catégories cinéma et audiovisuel"] = df.apply(attribuer_sous_categories_cinema, axis=1)



# In[42]:


##                  VÉRIFICATION DES RÉSULTATS 

# Filtrer les festivals pour lesquels la discipline dominante est "Cinéma, audiovisuel"
cinema_df = df[df["Discipline dominante"].str.contains("Cinéma, audiovisuel", na=False, case=False)]

# Afficher les premières lignes pour vérifier
print(cinema_df[["Nom du festival", "Discipline dominante", "Nouvelles sous-catégories cinéma et audiovisuel"]].head(50))


# Pour faciliter le travail et avoir une idée de la taille des données traitées, on compte ici : 
# * Le nombre de festivals ayant pour discipline dominante "Cinéma, audiovisuel". 
# * Le nombre de festivals dans chaque sous-catégorie. 

# In[43]:


# Compter les lignes où la colonne "Discipline dominante" contient "Cinéma, audiovisuel"
count_cinema_audiovisuel = df[df["Discipline dominante"].str.contains("audiovisuel", case=False, na=False)].shape[0]

# Afficher le résultat
print(f"Nombre total de festivals avec 'Cinéma, audiovisuel' : {count_cinema_audiovisuel}")


        # CINÉMA GÉNÉRALISTE LONG MÉTRAGE

# Compter les lignes où la sous-catégorie associée contient "Cinéma généraliste long métrage"
count_long = df["Nouvelles sous-catégories cinéma et audiovisuel"].apply(
    lambda x: "Cinéma généraliste long métrage" in x if isinstance(x, list) else False
).sum()

# Afficher le résultat
print(f"Nombre total de festivals ayant pour sous-catégorie 'Cinéma généraliste long métrage' : {count_long}")


        # CINÉMA GÉNÉRALISTE COURT MÉTRAGE

# Compter les lignes où la sous-catégorie associée contient "Cinéma généraliste court métrage"
count_court = df["Nouvelles sous-catégories cinéma et audiovisuel"].apply(
    lambda x: "Cinéma généraliste court métrage" in x if isinstance(x, list) else False
).sum()

# Afficher le résultat
print(f"Nombre total de festivals ayant pour sous-catégorie 'Cinéma généraliste court métrage' : {count_court}")


        # AUDIOVISUEL ET MÉDIAS

# Compter les lignes où la sous-catégorie associée contient "Audiovisuel et médias"
count_medias = df["Nouvelles sous-catégories cinéma et audiovisuel"].apply(
    lambda x: "Audiovisuel et médias" in x if isinstance(x, list) else False
).sum()

# Afficher le résultat
print(f"Nombre total de festivals ayant pour sous-catégorie 'Audiovisuel et médias' : {count_medias}")


        # FESTIVALS THÉMATIQUES

# Compter les lignes où la sous-catégorie associée contient "Festivals thématiques"
count_theme = df["Nouvelles sous-catégories cinéma et audiovisuel"].apply(
    lambda x: "Festivals thématiques" in x if isinstance(x, list) else False
).sum()

# Afficher le résultat
print(f"Nombre total de festivals ayant pour sous-catégorie 'Festivals thématiques' : {count_theme}")


        # CINÉMATOGRAPHIES DU MONDE

# Compter les lignes où la sous-catégorie associée contient "Cinématographies du monde"
count_monde = df["Nouvelles sous-catégories cinéma et audiovisuel"].apply(
    lambda x: "Cinématographies du monde" in x if isinstance(x, list) else False
).sum()

# Afficher le résultat
print(f"Nombre total de festivals ayant pour sous-catégorie 'Cinématographies du monde' : {count_monde}")


        # RESTROSPECTIVES ET CLASSIQUES

# Compter les lignes où la sous-catégorie associée contient "Rétrospectives et classiques"
count_retro = df["Nouvelles sous-catégories cinéma et audiovisuel"].apply(
    lambda x: "Rétrospectives et classiques" in x if isinstance(x, list) else False
).sum()

# Afficher le résultat
print(f"Nombre total de festivals ayant pour sous-catégorie 'Rétrospectives et classiques' : {count_retro}")


        # TECHNIQUES ET MÉTIERS

# Compter les lignes où la sous-catégorie associée contient "Techniques et métiers"
count_techniques = df["Nouvelles sous-catégories cinéma et audiovisuel"].apply(
    lambda x: "Techniques et métiers" in x if isinstance(x, list) else False
).sum()

# Afficher le résultat
print(f"Nombre total de festivals ayant pour sous-catégorie 'Techniques et métiers' : {count_techniques}")
    

        # CINÉMA ET MUSIQUE

# Compter les lignes où la sous-catégorie associée contient "Cinéma et musique"
count_cine_musique = df["Nouvelles sous-catégories cinéma et audiovisuel"].apply(
    lambda x: "Cinéma et musique" in x if isinstance(x, list) else False
).sum()

# Afficher le résultat
print(f"Nombre total de festivals ayant pour sous-catégorie 'Cinéma et musique' : {count_cine_musique}")


        # CINÉMA EXPÉRIMENTAL ET ARTS ASSOCIÉS

# Compter les lignes où la sous-catégorie associée contient "Cinéma expérimental et arts associés"
count_experimental = df["Nouvelles sous-catégories cinéma et audiovisuel"].apply(
    lambda x: "Cinéma expérimental et arts associés" in x if isinstance(x, list) else False
).sum()

# Afficher le résultat
print(f"Nombre total de festivals ayant pour sous-catégorie 'Cinéma expérimental et arts associés' : {count_experimental}")

            
        # JEUNES PUBLICS

# Compter les lignes où la sous-catégorie associée contient "Jeunes publics"
count_jeunes = df["Nouvelles sous-catégories cinéma et audiovisuel"].apply(
    lambda x: "Jeunes publics" in x if isinstance(x, list) else False
).sum()

# Afficher le résultat
print(f"Nombre total de festivals ayant pour sous-catégorie 'Jeunes publics' : {count_jeunes}")


        # ÉVÉNEMENTS ET PROJECTIONS SPÉCIALES 

# Compter les lignes où la sous-catégorie associée contient "Événements et projections spéciales"
count_special = df["Nouvelles sous-catégories cinéma et audiovisuel"].apply(
    lambda x: "Événements et projections spéciales" in x if isinstance(x, list) else False
).sum()

# Afficher le résultat
print(f"Nombre total de festivals ayant pour sous-catégorie 'Événements et projections spéciales' : {count_special}")



# **La catégorie Livre, littérature**

# In[44]:


# Problèmes dans les sorties "Sous catégorie non reconnue" à cause des virgules dans les parenthèses que le code prend pour un séparateur alors qu'il ne devrait pas. 

import re

def split_with_parentheses_handling(text):
    # Vérifier si le texte est valide
    if not isinstance(text, str) or not text.strip():
        return []
    
    # Diviser en utilisant la regex pour ignorer les virgules dans des parenthèses
    return re.split(r',\s*(?![^(]*\))', text.strip())


# In[45]:


import re  # Importer le module pour gérer les séparateurs multiples

# Dictionnaire élargi

regroupements_livre_litterature = {
    "Romans et Littérature Générale": [
        "Romans", "Littérature", "Essais", "Biographies", "Autobiographies", 
        "Poésie", "Recueils", "Nouvelles", "Textes littéraires", "essai", " autobiographie", "Littérature générale", "théâtre", "Fiction (roman, théâtre, etc.)", "Fiction", "Conte",
        "Non-fiction (documentaire, autobiographie, essai, récit, etc.)", "Généraliste", "Littérature et écriture contemporaine", 
        "Voyage", "Fictions", "Non fiction", "Tout les genres",
        "Littérature contemporaine", "Rentrée littéraire littérature générale", "Création littéraire",
"Littérature blanche", "Fictions (romans, théâtre, etc.)",
        "Fictions (roman, théâtre, etc.) Non-fiction (documentaire, autobiographie, essai, récit, etc.)",    "Actualité littéraire", "Livre ancien",      "Poésie contemporaine", "Oulipo", "Littérature performative",
        "Littérature langue française", "Rentrée littéraire littérature generale", "Fiction (romans théâtre etc)", "Fiction (roman, théâtre, etc.) Non-fiction (documentaire, autobiographie, essai, récit, etc.)",
        "Tous genres littéraires", "Ecritures contemporaines pour le théâtre", "Non-fiction", "Littérature langue étrangère ; Littérature langue française", "Pas de genre définie",
        "Écritures contemporaines", "new romance", "Autre", "Autres", "autres", "Autre : Poésie contemporaine", "Conte ; non-fiction", "non-fiction", "Montagne aventures"

    ],
    "Bandes Dessinées et Illustrations": [
        "Bandes dessinées", "Mangas", "Comics", "Illustrations", "Graphic novels", 
        "Dessins de presse", "Albums illustrés", "manga", " Bande dessinée", "Bande-dessinée", "Livre d'artistes", "livre d'art", "livres d'artistes",
        "micro-édition et images imprimées", "animé", "Bande dessiné", "Bande déssinée", "BD et livres jeunesse", "Rencontres du 9e art", "Zébuli salon de illustration et BD jeunesse", "Art lyrique ; bandes dessinées", "Manga et culture asiatique",         "Livre d’artiste et image imprimée",     
        "Livre d'artiste", "Bande dessinée & arts associés" 

    ],
    "Jeunesse et Jeune Public": [
        "Littérature jeunesse", "Contes", "Livres pour enfants", "Histoires pour jeunes", 
        "Albums jeunesse", "Contes musicaux", "Ciné-contes", "Jeunesse", " jeunesse", "Littérature exclusivement jeunesse", "Jeune public", "Littérature jeunesse en général", "Albums et illustrations jeunesse",
        "Littérature jeunesse - petite enfance", "Album jeunesse", "Enfance jeunesse",
        "Petite enfance", "Raconte bébés", "Festival jeune public et famille", "littérature générale et littérature jeunesse", "littérature très petite enfance",
        "Albums et illustratilns jeunesse", "jeunesse ; environnement"

    ],
    "Policier et Thriller": [
        "Littérature policière", "Thrillers", "Romans noirs", "Mystères", "Enquêtes", "Polar", "Policier"
    ],
    "Science-Fiction et Fantasy": [
        "Science-fiction", "Fantasy", "Fantastique", "Sagas", "Univers imaginaires", 
        "Épopées", "Steampunk", "Imaginaire",     "Science fiction", "SF", "Épouvante"
    ],
    "Littératures régionales et du Monde": [
        "Littérature étrangère", "Littératures européennes", "Littératures asiatiques", 
        "Littératures africaines", "Littératures américaines", "Traditions orales", "littérature régionale", "Littérature-monde", "Russophonie et francophonie", "Carnet et littérature de voyage", "Histoire - mer - aventures etc", "Récits de voyage",
        "Animations autour de la langue gallèse"

    ],
    "Édition et Métiers du Livre": [
        "Édition", "Auto-édition", "Librairies", "Ateliers d'écriture", 
        "Typographie", "Illustrations éditoriales", "Métiers du livre", "Livres d'artistes / Petite édition", "Éditions d'art, livres d'artistes"

    ],
    "Conférences et Rencontres Littéraires": [
        "Rencontres avec auteurs", "Lectures publiques", "Conférences", "Ateliers littéraires", 
        "Échanges littéraires", "Tables rondes", "Dédicaces", "Eloquence", "lecture", "Lecture à voix haute", "Traduction littéraire", "littérature de critique sociale",
        "philosophie", "lecture à voix haute", "salon du livre", "Expositions", "Rencontres", "Salon de rencontre des auteurs de théâtre et cinéma", "Rencontres littéraires",         "Lectures", "Lectures musicales", "Performances",
        "Le festival propose aussi des lectures", "débats et ateliers", "scène", "ateliers", "Jeux de rôle", "jeux de plateaux", "ateliers", "bibliophilie"
    ],

    "Histoire et Patrimoine Littéraire": [
        "Archives", "Histoire du livre", "Manuscrits", "Bibliothèques historiques", 
        "Littératures classiques", "Récits historiques", "Textes anciens", "Livre ancien", "Histoire", "Histoire et patrimoine", "Histoire et sciences humaines", "historique"
    ],

    "Pluridisciplinaire : arts et littératures croisés ": [
        "Pluridisciplinaire", "Livre et arts visuels", "Livres et vin", "Art lyrique ; bandes dessinées ; musique savante ; audiovisuels", "Art",         "Art lyrique ; musique savante", "Musique", "Art lyrique ; musiques actuelles ; théâtre",
        "Art lyrique ; danse modern jazz ; jazz et musiques improvisées ; musique savante ; théâtre",
    "Art lyrique ; jazz ; musique savante ; musiques de films", "Livre et vin"
        "Art lyrique ; jazz ; jazz et musiques improvisées ; musique classique", "Art lyrique ; jazz ; jazz et musiques improvisées ; musique (d'harmonie) ; musique classique ; musique savante ; musiques traditionnelles", "Tous genres littéraires et animations dépendant de la thématique",         "Littérature scientifique", "Sciences humaines", "Sociales", "Lettres", "Sciences fondamentales", "Développement personnel", "Bien-être", "Pas de sous-catégorie", "Toutes thématiques",
        "Pas de sous catégorie", "Art lyrique ; danse modern' jazz ; jazz et musiques improvisées ; musique savante ; théâtre", "livre audio", "Littératures et Pratiques Culturelles",
        "Art lyrique (du congo) ; audiovisuel-cinéma (musiques innovatrices) ; danse contemporaine ; musique (musiques innovatrices) ; musique expérimentale ; musiques actuelles (musiques innovatrices) ; pop (hybride alchimérique) ; rock (avant-garde) ; slam / spoken word ; techno (cosmique) ; théâtre",
        "Livre et vin", "de mettre en avant les liens étroits et riches qu’entretiennent musique et littérature.", "films", "Art lyrique ;", "spectacles", "jeux", "Culture"
    
]
}

# Ignorer Sous-catégorie non reconnue : 'tous les genres si marseille est présente dans le livre' pour le festival 'Carré des écrivains'
# Ignorer Sous-catégorie non reconnue : 'sciences' pour le festival 'Formula Bula, bande dessinée et plus si affinités'
# Ignorer Sous-catégorie non reconnue : 'balade fluviale' pour le festival 'Formula Bula, bande dessinée et plus si affinités'
# Ignorer Sous-catégorie non reconnue : 'visites guidées' pour le festival 'Formula Bula, bande dessinée et plus si affinités'
# Ignorer Sous-catégorie non reconnue : 'sociale' pour le festival 'Salon du livre et de l'illustration'
# Ignorer, déjà catégorisé. Sous-catégorie non reconnue : 'concerts' pour le festival 'Festival Livres & Musiques de Deauville'
# Ignorer, déjà catégorisé. Sous-catégorie non reconnue : 'émergence' pour le festival 'DIRE'
# Ignorer, déjà catégorisé. Sous-catégorie non reconnue : 'française et étrangère' pour le festival 'Rencontres Adriatiques'


# Inverser le dictionnaire pour une recherche efficace
inverse_regroupements = {}
for categorie, sous_cats in regroupements_livre_litterature.items():
    for sous_cat in sous_cats:
        inverse_regroupements[sous_cat.lower().strip()] = categorie

# Fonction pour attribuer les sous-catégories
def attribuer_sous_categories(row):
    if "Livre" not in str(row.get("Discipline dominante", "")):
        return None  # Si ce n'est pas du spectacle vivant, ne rien faire
    
    sous_categorie = row.get("Sous-catégorie livre et littérature")
    if pd.isna(sous_categorie):  # Si la sous-catégorie est NaN
        return None
    
    sous_categories = split_with_parentheses_handling(str(sous_categorie))  # Diviser en cas de multiples sous-catégories
    nouvelles_categories = set()
    for sous_cat in sous_categories:
        sous_cat_normalise = sous_cat.lower().strip()  # Normaliser : minuscule et sans espaces
        if sous_cat_normalise in inverse_regroupements:
            nouvelles_categories.add(inverse_regroupements[sous_cat_normalise])
        else:
            # Débogage pour les sous-catégories non reconnues
            print(f"Sous-catégorie non reconnue : '{sous_cat}' pour le festival '{row['Nom du festival']}'")
    return list(nouvelles_categories) if nouvelles_categories else None

# Appliquer la fonction uniquement si Discipline dominante contient "Spectacle vivant"
df["Nouvelles sous-catégories livre et littérature"] = df.apply(attribuer_sous_categories, axis=1)




# Citéphilo à ajouter à la main ; formule BUla 


# In[46]:


##                  VÉRIFICATION DES RÉSULTATS 

# Filtrer les festivals pour lesquels la discipline dominante est "Livre, littérature"
livre_df = df[df["Discipline dominante"].str.contains("Livre", na=False, case=False)]

# Afficher les premières lignes pour vérifier
print(livre_df[["Nom du festival", "Discipline dominante", "Nouvelles sous-catégories livre et littérature"]].head(50))


# Pour faciliter le travail et avoir une idée de la taille des données traitées, on compte ici : 
# * Le nombre de festivals ayant pour discipline dominante "Livre, littérature". 
# * Le nombre de festivals dans chaque sous-catégorie. 

# In[47]:


# Compter les lignes où la colonne "Discipline dominante" contient "Livre, littérature"
count_livre_litterature = df[df["Discipline dominante"].str.contains("Livre", case=False, na=False)].shape[0]

# Afficher le résultat
print(f"Nombre total de festivals avec 'Livre, littérature' : {count_livre_litterature}")
   

        # ROMAN ET LITTÉRATURE GÉNÉRALE

# Compter les lignes où la sous-catégorie associée contient "Romans et Littérature Générale"
count_roman = df["Nouvelles sous-catégories livre et littérature"].apply(
    lambda x: "Romans et Littérature Générale" in x if isinstance(x, list) else False
).sum()

# Afficher le résultat
print(f"Nombre total de festivals ayant pour sous-catégorie 'Romans et Littérature Générale' : {count_roman}")


        # BANDES DESSINÉES ET ILLUSTRATIONS

# Compter les lignes où la sous-catégorie associée contient "Bandes Dessinées et Illustrations"
count_bd = df["Nouvelles sous-catégories livre et littérature"].apply(
    lambda x: "Bandes Dessinées et Illustrations" in x if isinstance(x, list) else False
).sum()

# Afficher le résultat
print(f"Nombre total de festivals ayant pour sous-catégorie 'Bandes Dessinées et Illustrations' : {count_bd}")


        # JEUNESSE ET JEUNE PUBLIC

# Compter les lignes où la sous-catégorie associée contient "Jeunesse et Jeune Public"
count_jeunesse = df["Nouvelles sous-catégories livre et littérature"].apply(
    lambda x: "Jeunesse et Jeune Public" in x if isinstance(x, list) else False
).sum()

# Afficher le résultat
print(f"Nombre total de festivals ayant pour sous-catégorie 'Jeunesse et Jeune Public' : {count_jeunesse}")


        # POLICIER ET THRILLER

# Compter les lignes où la sous-catégorie associée contient "Policier et Thriller"
count_policier = df["Nouvelles sous-catégories livre et littérature"].apply(
    lambda x: "Policier et Thriller" in x if isinstance(x, list) else False
).sum()

# Afficher le résultat
print(f"Nombre total de festivals ayant pour sous-catégorie 'Policier et Thriller' : {count_policier}")


        # SCIENCE-FICTION ET FANTASY

# Compter les lignes où la sous-catégorie associée contient "Science-Fiction et Fantasy"
count_fantasy = df["Nouvelles sous-catégories livre et littérature"].apply(
    lambda x: "Science-Fiction et Fantasy" in x if isinstance(x, list) else False
).sum()

# Afficher le résultat
print(f"Nombre total de festivals ayant pour sous-catégorie 'Science-Fiction et Fantasy' : {count_fantasy}")


        # LITTÉRATURES RÉGIONALES ET DU MONDE

# Compter les lignes où la sous-catégorie associée contient "Littératures régionales et du Monde"
count_monde = df["Nouvelles sous-catégories livre et littérature"].apply(
    lambda x: "Littératures régionales et du Monde" in x if isinstance(x, list) else False
).sum()

# Afficher le résultat
print(f"Nombre total de festivals ayant pour sous-catégorie 'Littératures régionales et du Monde' : {count_monde}")


        # ÉDITIONS ET MÉTIERS DU LIVRE

# Compter les lignes où la sous-catégorie associée contient "Édition et Métiers du Livre"
count_edition = df["Nouvelles sous-catégories livre et littérature"].apply(
    lambda x: "Édition et Métiers du Livre" in x if isinstance(x, list) else False
).sum()

# Afficher le résultat
print(f"Nombre total de festivals ayant pour sous-catégorie 'Édition et Métiers du Livre' : {count_edition}")
   

        # CONFÉRENCES ET RENCONTRES LITTÉRAIRES

# Compter les lignes où la sous-catégorie associée contient "Conférences et Rencontres Littéraires"
count_conf = df["Nouvelles sous-catégories livre et littérature"].apply(
    lambda x: "Conférences et Rencontres Littéraires" in x if isinstance(x, list) else False
).sum()

# Afficher le résultat
print(f"Nombre total de festivals ayant pour sous-catégorie 'Conférences et Rencontres Littéraires' : {count_conf}")


        # HISTOIRE ET PATRIMOINE LITTÉRAIRE

# Compter les lignes où la sous-catégorie associée contient "Histoire et Patrimoine Littéraire"
count_histoire = df["Nouvelles sous-catégories livre et littérature"].apply(
    lambda x: "Histoire et Patrimoine Littéraire" in x if isinstance(x, list) else False
).sum()

# Afficher le résultat
print(f"Nombre total de festivals ayant pour sous-catégorie 'Histoire et Patrimoine Littéraire' : {count_histoire}")


        # PLURIDISCIPLINAIRE : ARTS ET LITTÉRATURES CROISÉS

# Compter les lignes où la sous-catégorie associée contient "Pluridisciplinaire : arts et littératures croisés"
count_pluridisc = df["Nouvelles sous-catégories livre et littérature"].apply(
    lambda x: "Pluridisciplinaire : arts et littératures croisés" in x if isinstance(x, list) else False
).sum()

# Afficher le résultat
print(f"Nombre total de festivals ayant pour sous-catégorie 'Pluridisciplinaire : arts et littératures croisés' : {count_pluridisc}")


# **La catégorie Musique**

# In[48]:


# Problèmes dans les sorties "Sous catégorie non reconnue" à cause des virgules dans les parenthèses que le code prend pour un séparateur alors qu'il ne devrait pas. 

import re

def split_with_parentheses_handling(text):
    # Vérifier si le texte est valide
    if not isinstance(text, str) or not text.strip():
        return []
    
    # Diviser en utilisant la regex pour ignorer les virgules dans des parenthèses
    return re.split(r',\s*(?![^(]*\))', text.strip())


# In[49]:


import re
import re

# Dictionnaire élargi
regroupements_musique = {
    "Musique classique et opéra": [
        "Musique classique", "Opéra", "Musique baroque", "Musique romantique", "Concerts symphoniques", 
        "Chanson ou variété française", "Musiques classiques et savantes", "Musique savante", 
        "Art lyrique", "Musiques classiques", "Musiques anciennes", "Musique chorale classique et contemporaine",
        "Musique sacrée", "Musiques baroques", "Musiques classiques avec voix", "Chant choral", 
        "Musiques classiques et contemporaines", "Opéras et concerts lyriques", 
        "Classique revisité", "Art vocal", "Musique ancienne", "classique", "Classique", "Musique ancienne", "Opérettes", "Variétés (folklores du monde)", 
        "Savantes", "Concerts classique gospel", "Musique sacrée et profane", "Musique savante occidentale", "Gospel/spiritual", "gospel/spiritual ", "Chœurs", "Chœurs d'enfants", "Musique sacrée et chants baroques", 
       "Gospel", "Art choral", " opéras", "musique classique (folklores du monde) ", " chants gospels", 'Opérette', "Voix lyrique",
       "11- Musique classique", "lyrique", "Art lyrique ; musique ; musique classique ; musiques actuelles", "Musique baroque ; Musique classique", "Musique classique ; musique savante ; théâtre",
       "Musique classique, Musique contemporaine, Musiques traditionnelles, Opéra", "11- Musique classique, lyrique, contemporaine, autres", "ensembles classiques / jazz / baroques",
       "Musique Lyrique", "Musique sacree", "Musiques et chants baroques et/ou sacrés", "Chant - Gospel", "Danse Classique", "Musiques classiques et jazz", "baroque", "Musiques de répertoire et de création", "Harmonies", "gospel et compositeurs contemporains également proposés au public", "Musiques sacrées et profanes", "operette et comédie musicale américaine", "Orgues / Musique classique",
        "Musique de répertoire", "Musiques lyriques", "Musiques et lyrique", "Musique savante (musique ancienne, classique, contemporaine autour de l'orgue)", "ensemble vocal a cappella international", "Chant lyrique", "Musiques classiques piano", "classiques et romantiques mais on entend aussi des arrangements de classiques du rock", "baroques et contemporaines", "Musiques classiques / Jazz",
        "musique de traverse"


    ],

    "Musiques actuelles et populaires": [
        "Pop", "Hip-hop", "Rap", "Chanson française", "Musique contemporaine", "Musique expérimentale", 
        "Musiques actuelles", "slam", "07- Musiques actuelles sans distinction", 
        "09- Pluridisciplinaire", "01- Chanson", "08- Musiques (sans distinction esthétique)", 
        "Musiques actuelles sans distinction", "Musique",  "Dub", "Ska", 
         "Funk", "Variété française", "Chanson", "Musiques contemporaines", "Terme générique : musiques actuelles",
        "Cultures hip-hop et urbaines", "Musique contemporaine/expérimentale", "Pluridisciplinaire", "Autres Musiques", "Expérimentales", 
        "Improvisation", "Musiques improvisées", "Chanson et poésie francophones", "Musique contemporaine et création sonore", "Tous genres confondus",
        "Chansons",  "Chansons festives", "Chanson ou variété française Musiques du monde Pop", "musiques", "Musique pluridisciplinaire", "chant",
        "Musique actuelle", "Variétés", "Hip hop",  "Musiques diverses", "Musiquse actuelles",  "Musiques diversifiées", "Impro libre", "Musiques (sans distinction esthétique)",
        "Musique actuelles", "Musiques inclassables", "contemporaine", "contemporaines", "Chanson ou variétés françaises", "hip-hop / rap", "Hip-hop/rap", "autres",
        "musiques actuelles (festives, rock, reggae... )", "slam / spoken word", "cultures urbaines", "Toutes les formes musicales", "Autre", "musiques d'aujourd'hui (musique contemporaine)",
        "répertoires diversifiés - blues - chanson - world - .....", "Musiques actuelles - jazz", "Les Agités du Mélange ont pour essence de mélanger les genre justement", "mélange de plusieurs genres", "Pluridisciplinaire culture", "Eclectique", "Musiques actuelles (blues, rock alternatif & indépendant)", "Musiques actuelles d'influence traditionnelle", "chansons", "Musique pluridisciplinaire"


        
    ],    

    "Musiques du monde": [
        "Musique africaine", "Musique asiatique", "Musique latine", "Musique celtique",
        "Musique méditerranéenne", "Musique des Caraïbes", "Musiques traditionnelles", 
        "Musiques du monde", "Variétés internationales", "04- Musiques traditionnelles et du monde", 
        "Musiques des Balkans", "Musiques tziganes", "Flamenco", "Chants basques", 
        "Musiques traditionnelles et du monde", "Musiques slaves", "Musiques méditerranéennes", "Musique du monde", "Culture hispanique et latino-américaine", "Musique world music", 
        "Chant traditionnel", "Musiques du Monde et Trad", "Thème culture hispanique", 
        "Musique du mondes", "Musiques du monde (berbère)", "Jazz (folklores du monde)", 
        "Soul/funk (folklores du monde)", "Musiques traditionnelles (folklores du monde)", "Musique traditionnelle régionale",
        "Thème culture hispanique", 
        "Musiques afro-caribéennes", "Musiques créoles", "Musique tzigane", "Chants traditionnels d'Afrique", "Variété internationale", " musique (folklores du monde) ",
        "traditions catalanes", "culture Amériques-Caraïbes", "Gypsy", "Musiques du monde ; musiques traditionnelles", "chansons hispaniques et catalanes",
        "Concert autour du Tango Argentin", "du monde", "Tango", "Autour de la culture créole", "Afrobeat", "musique brésilienne", "flamenco (musique)", "gypsie", "musiques traditionnelles afrique sub-sahariennes", "musiques traditionnelles amérique latine", "swing funk afro caribeene", "musiques traditionnelles d'irlande", "jazz et de musiques du monde", "du spectacle et du patrimoine Tsigane", "musique brésilienne", "Musique cubaine", "Musiques traditionnelles de corse", "musiques traditionnelles amérique latine", "musiques traditionnelles europe centrale et est", "musiques traditionnelles du kurdistan", "musique du monde et jazz",
        "Percussions du monde", "bals latinos", "zumba", "Culture trans-territoriale", "Musique du minde", "du jazz ou de compositeurs cubains et latino-américains.", "Musique Afro américaine", "afro"


    ],

    "Jazz, blues, RnB": [
        "Jazz", "Blues", "Swing", "Bossa nova", "RnB", "R'n'B", "03- Jazz", 
        "Jazz manouche", "Latin jazz", "Jazz et musiques improvisées", "Blues et musiques improvisées", "Reggae", "Reggae / Dub / Ska / Soul / Funk / World",
        "Rockabilly - Country - R'n'R - Rhythm & Blues",  "Reggae", "Jazz Blues", "Jazz et classique", "Jazz et musiques du monde",
        "Musique Jazz", "Musique afro jazz", "Reggae / Dub / Ska / Soul / Funk  / World", "Reggae / Dub", "Jazz caribéen", "Jazz et vin",
        "Chanson française jazz", "Jazz / musiques improvisées", 
        "Jazz européen et américain", "Musiques afrobeat et jazz", "soul", "03- Jazz, blues et musiques improvisées", "Jazz, blues", "chanson francaise jazz", "jazz et contemporain",
        "soul/funk", "jazz chanson musique du monde danse", "concert jazz", "Musiques classiques et jazz", "Musiques actuelles - jazz", "jazz et de musiques du monde", "Musiques Cajun - Zydeco - Swamp Pop", "swing/middle jazz", "musique du monde et jazz",
        "rock Jazz", "du jazz ou de compositeurs cubains et latino-américains.", "Musiques classiques / Jazz", "ragga"



    ],


    "Musique rock et métal": [
        "Rock", "Indie", "Hard rock", "Métal", "Rock progressif", "Garage Rock", "Punk", "Rock pop Electro", "Rock progressif", "Rockabilly", 
         "Electro / rock", "Punk-rock", "Rock festif", "Heavy Metal", 
        "Jazz-rock", "Metal (néo classique)", "Rock pop électro", "Metal",   "Punk rock",  "Post-rock", "Math-rock", "Punk rock", "Hardcore punk",
        "rock et rock progressif", " rock (folklores du monde) ", "Punk...", "Rock Country", "Hardcore", "rock pop", "rock celtique", "Folk-rock",
        "Musiques indépendantes (pop - rock - punk - garage - électro)", "hardcore", "pop/rock en orchestre symphonique", "rock Jazz'", "Fusion", "musique (fusion)"


    ],

    "Musique instrumentale": [
        "Guitare acoustique", "Piano", "Musique de chambre", "Orchestrations", 
        "Orgue", "Trompette et orgue", "Concerts avec piano ou claviers", "Concours de piano", "Guitare", "Ensembles de tambours", "Fifres et tambours", "Fifres et percussions", 
        "Batterie-Fanfare", "Fanfare", "Cuivres et percussions", "Orchestres d'harmonie", "Musique acousmatique / electroacoustique / concrète", "Improvisés",
         "Violon", "Orgue", "Les cuivres sous toutes leurs formes : harmonies", "FANFARES de divers styles", "fanfares", "tout type musical mais uniquement en composition",
         "tous concerts avec piano ou claviers", "cuivres", "Brass band", "Cuivres", "Mlusique d'orgue","Percussions du monde", "Musiques classiques piano", "Musiques acoustiques", "percussions", "accordéon"



    ],


    "Musique et festivals thématiques": [
        "Ciné-concerts", "Festivals de musique", "Concerts en plein air", 
        "Comédies musicales", "Performances musicales", "Musique et littérature", 
        "Théâtre musical", "Comédie musicale", "Concerts autour du Tango Argentin", "Spectacle vivant", "Danse", "Arts de la rue", "Musique et sport outdoor",
        "Moto concert rock parties de poker", 
        "Bons fromages et bonne musique (rock)", "Une soirée", "Humour", "Et 1 journée dédiée aux Arts de la Rue", 
        "Théâtre", "Performance", "Exposition", "Art", "Fête de la ville", "Feria", "Fête votive", "Fête de la pomme",  
        "Spectacles multiculturels culture africaine", "Musique indépendante", "Théâtre baroque", 
        "Musique/Spectacle vivant/Littérature/Arts visuels", "Musiques actuelles/stand up", "Musique indépendante", "Alternative", "Improvisation théâtrale", "Arts visuels",
        "Humour et musique", "Musique Cinéma", "Festival International de Piano", "Spectacles multiculturels culture africaine",
        "motos", "poker", "fetes nocturnes", "Littérature", "performance - installation", "14- Autres disciplines culturelles (arts plastiques, cinéma, photographie, livre...)",
        "13- Autres spectacles (théâtre, arts de la rue et du cirque...)", "05- Humour", "10- Comédie musicale",
        "15- Fête de la ville", "1 altitude 1 ambiance musicale (soit 3 ambiances différentes)", "musique de rue", "théâtre d'humour/café-théâtre", "lecture publique (théâtre)", "danse et chants", "parité homme-femme",
        "experimentales", "Musique de création", "degustation de vin et jazz", "Autres spectacles (théâtre, arts de la rue et du cirque...)", "expérimentale", "cirque", "arts de rue", "bals", "Spectacle danse", "concours de guitare theme l'espagne", "Musiques de films", "musiques de création / musiques expérimentales (déjà, votre enquête fait l'impasse sur un secteur/une filière...)", "théatre et musique", "Musiques improvisées et expérimentales", "cinéma", "Festival pluridisciplinaire : arts visuels", "pour la cause aninal humour et musique",
        "Musiques vivantes", "ciné-concert", "spectacle déambulatoire", "théâtre de rue", "danses", "repas gascons", "concerts gratuits", "ateliers de création", "jeux", "animation musicales",
        "chants", "expositions", "stages de danses .", "THEATRE MUSICAL", "Danse et musique", "féministe et citoyen", "Carnaval", "chorégraphies et contes", "soirée danse", "voix", "impros"


    ],

    "Musiques électroniques": [
        "Techno", "House", "Ambient", "EDM", "Minimal", "Trance", "Musiques amplifiées ou électroniques", 
        "Musiques électroniques", "Musique électronique", "02- Musiques amplifiées ou électroniques", 
        "Electroacoustique", "Musiques électroniques et hip-hop", "Electro", "Pop électro", "Sound System Dub", "Musique contemporaine/électroniques/indépendantes",
        "Musique électroacoustique", "Dub...", "Musiques expérimentales",
        "Electroniques", "Musiques électroniques ; numérique", "Musiques actuelles ; musiques électroniques", "musique contemporaine/électoniques/indépendantes", "Trip Hop", "trip hop", "Musiques actuelles et électroniques", "natural trance"

    ],

    "Musique pour jeunes publics": [
        "Chansons pour enfants", "Concerts pédagogiques", "Spectacles musicaux pour jeunes publics", 
        "Musique pour jeunes publics", "Jeune public", "Rock pour enfants", "Jeune Public musiques actuelles", "musiques et spectacles à destination du jeune public",
        "spectacle pour enfants", "marionnettes"


    ],

    "Musiques folk et patrimoniales": [
        "Musique médiévale", "Musique de la Renaissance", "Musique traditionnelle régionale", 
        "Folk", "Musique acoustique", "Chants traditionnels", "Ballades", 
        "Musiques anciennes", "Musique traditionnelle", "Musiques traditionnelles et du monde", "Bluegrass", "Old-Time", "Cajun", "Musiques traditionnelles fusion", 
        "Musique celtique et d'Occitanie", "Traditions", "Gospel et Polyphonies", "Musique anciennes", "Musiques sacrées", "Musiques sacrees", "LE SÉNÉGAL SA MUSIQUE",
        "SES DANSES", "SA CULTURE", "Musique Country", "Chanson (folk)", "Country", "Country music", "musiques traditionelles",  "Oldtime", "pagan folk", "Folk-rock", "Musiques traditionnelles de France",
        "musique improvisée / folklore imaginaire", "Danses traditionnelles", "Culture trans-territoriale", "fête traditionnelle de gascogne - bal - musique et danse"


    ]
}


# Inverser le dictionnaire pour une recherche efficace
inverse_regroupements = {}
for categorie, sous_cats in regroupements_musique.items():
    for sous_cat in sous_cats:
        inverse_regroupements[sous_cat.lower().strip()] = categorie


# Mise à jour de la fonction split_with_parentheses_handling
def split_with_parentheses_and_commas_handling(s):
    """
    Divise une chaîne en utilisant les séparateurs ',' et ';' tout en respectant le contenu entre parenthèses.
    """
    # Remplacer les séparateurs `;` et `,` par un unique séparateur `;`
    s = re.sub(r",\s*(?![^(]*\))", ";", s)  # Remplacer les ',' qui ne sont pas dans des parenthèses
    s = re.sub(r";\s*", ";", s)  # Uniformiser les séparateurs
    return [part.strip() for part in s.split(";") if part.strip()]  # Diviser et nettoyer

# Fonction principale avec la mise à jour
def attribuer_sous_categories(row):
    if "Musique" not in str(row.get("Discipline dominante", "")):
        return None  # Si ce n'est pas de la musique, ne rien faire

    # Déterminer quelle colonne utiliser
    sous_categorie = row.get("Sous-catégorie musique")
    if pd.isna(sous_categorie) or sous_categorie.strip().lower() == "musiques actuelles":
        sous_categorie = row.get("Sous-catégorie Musique CNM")  # Utiliser la colonne CNM si condition remplie

    if pd.isna(sous_categorie):  # Si la sous-catégorie est NaN
        return None

    # Diviser les sous-catégories multiples avec gestion des parenthèses, des points-virgules et des virgules
    sous_categories = split_with_parentheses_and_commas_handling(str(sous_categorie))
    nouvelles_categories = set()
    for sous_cat in sous_categories:
        sous_cat_normalise = sous_cat.lower().strip()  # Normaliser : minuscule et sans espaces
        if sous_cat_normalise in inverse_regroupements:
            nouvelles_categories.add(inverse_regroupements[sous_cat_normalise])
        else:
            # Débogage pour les sous-catégories non reconnues
            print(f"Sous-catégorie non reconnue : '{sous_cat}' pour le festival '{row['Nom du festival']}'")
    return list(nouvelles_categories) if nouvelles_categories else None

# Appliquer la fonction sur le DataFrame
df["Nouvelles sous-catégories musique"] = df.apply(attribuer_sous_categories, axis=1)


# In[50]:


##                  VÉRIFICATION DES RÉSULTATS 

# Filtrer les festivals pour lesquels la discipline dominante est "Musique"
musique_df = df[df["Discipline dominante"].str.contains("Musique", na=False, case=False)]

# Afficher les premières lignes pour vérifier
print(musique_df[["Nom du festival", "Discipline dominante", "Nouvelles sous-catégories musique"]].head(50))


# In[51]:


# Compter les lignes où la colonne "Discipline dominante" contient "Musique"
count_musique_dom = df[df["Discipline dominante"].str.contains("Musique", case=False, na=False)].shape[0]

# Afficher le résultat
print(f"Nombre total de festivals avec 'Musique' : {count_musique_dom}")
   

        # MUSIQUE CLASSIQUE ET OPÉRA

# Compter les lignes où la sous-catégorie associée contient "Musique classique et opéra"
count_opera = df["Nouvelles sous-catégories musique"].apply(
    lambda x: "Musique classique et opéra" in x if isinstance(x, list) else False
).sum()

# Afficher le résultat
print(f"Nombre total de festivals ayant pour sous-catégorie 'Musique classique et opéra' : {count_opera}")


        # MUSIQUES ACTUELLES ET POPULAIRES

# Compter les lignes où la sous-catégorie associée contient "Musiques actuelles et populaires"
count_actuelles = df["Nouvelles sous-catégories musique"].apply(
    lambda x: "Musiques actuelles et populaires" in x if isinstance(x, list) else False
).sum()

# Afficher le résultat
print(f"Nombre total de festivals ayant pour sous-catégorie 'Musiques actuelles et populaires' : {count_actuelles}")


        # MUSIQUES DU MONDE

# Compter les lignes où la sous-catégorie associée contient "Musiques du monde"
count_monde = df["Nouvelles sous-catégories musique"].apply(
    lambda x: "Musiques du monde" in x if isinstance(x, list) else False
).sum()

# Afficher le résultat
print(f"Nombre total de festivals ayant pour sous-catégorie 'Musiques du monde' : {count_monde}")


        # JAZZ, BLUES, RNB

# Compter les lignes où la sous-catégorie associée contient "Jazz, blues, RnB"
count_jazz = df["Nouvelles sous-catégories musique"].apply(
    lambda x: "Jazz, blues, RnB" in x if isinstance(x, list) else False
).sum()

# Afficher le résultat
print(f"Nombre total de festivals ayant pour sous-catégorie 'Jazz, blues, RnB' : {count_jazz}")


        # MUSIQUE ROCK ET MÉTAL

# Compter les lignes où la sous-catégorie associée contient "Musique rock et métal"
count_metal = df["Nouvelles sous-catégories musique"].apply(
    lambda x: "Musique rock et métal" in x if isinstance(x, list) else False
).sum()

# Afficher le résultat
print(f"Nombre total de festivals ayant pour sous-catégorie 'Musique rock et métal' : {count_metal}")


        # MUSIQUE INSTRUMENTALE

# Compter les lignes où la sous-catégorie associée contient "Musique instrumentale"
count_instru = df["Nouvelles sous-catégories musique"].apply(
    lambda x: "Musique instrumentale" in x if isinstance(x, list) else False
).sum()

# Afficher le résultat
print(f"Nombre total de festivals ayant pour sous-catégorie 'Musique instrumentale' : {count_instru}")
  

        # MUSIQUE ET FESTIVALS THÉMATIQUES

# Compter les lignes où la sous-catégorie associée contient "Musique et festivals thématiques"
count_tm = df["Nouvelles sous-catégories musique"].apply(
    lambda x: "Musique et festivals thématiques" in x if isinstance(x, list) else False
).sum()

# Afficher le résultat
print(f"Nombre total de festivals ayant pour sous-catégorie 'Musique et festivals thématiques' : {count_tm}")
  

        # MUSIQUES ÉLECTRONIQUES

# Compter les lignes où la sous-catégorie associée contient "Musiques électroniques"
count_electro = df["Nouvelles sous-catégories musique"].apply(
    lambda x: "Musiques électroniques" in x if isinstance(x, list) else False
).sum()

# Afficher le résultat
print(f"Nombre total de festivals ayant pour sous-catégorie 'Musiques électroniques' : {count_electro}")


        # MUSIQUE POUR JEUNES PUBLICS

# Compter les lignes où la sous-catégorie associée contient "Musique pour jeunes publics"
count_jp = df["Nouvelles sous-catégories musique"].apply(
    lambda x: "Musique pour jeunes publics" in x if isinstance(x, list) else False
).sum()

# Afficher le résultat
print(f"Nombre total de festivals ayant pour sous-catégorie 'Musique pour jeunes publics' : {count_jp}")


        # MUSIQUES FOLK ET PATRIMONIALES

# Compter les lignes où la sous-catégorie associée contient "Musiques folk et patrimoniales"
count_folk = df["Nouvelles sous-catégories musique"].apply(
    lambda x: "Musiques folk et patrimoniales" in x if isinstance(x, list) else False
).sum()

# Afficher le résultat
print(f"Nombre total de festivals ayant pour sous-catégorie 'Musiques folk et patrimoniales' : {count_folk}")


# In[52]:


print(df.head())


# ### <u>4. Supression des anciennes colonnes  <u>

# In[53]:


colonnes_a_supprimer = ["Sous-catégorie spectacle vivant", "Sous-catégorie musique", "Sous-catégorie arts visuels et arts numériques", "Sous-catégorie livre et littérature", "Sous-catégorie cinéma et audiovisuel", "Sous-catégorie Musique CNM"]

df = df.drop(columns = colonnes_a_supprimer)

print(df.columns)


# In[54]:


if __name__ == "__main__":
    # Assurez-vous que df existe bien à la fin de ce fichier
    pass


# ### <u>5. Bon format de la colonne période  <u>

# In[55]:


# Modifier la colonne pour ajouter une majuscule au début des périodes
df["Période principale de déroulement du festival"] = df["Période principale de déroulement du festival"].replace({
    "avant-saison (1er janvier - 20 juin)": "Avant-saison (1er janvier - 20 juin)",
    "saison (21 juin - 5 septembre)": "Saison (21 juin - 5 septembre)",
    "après-saison (6 septembre - 31 décembre)": "Après-saison (6 septembre - 31 décembre)"
})

# Vérifier les valeurs uniques après modification
print("Valeurs après modification :")
print(df["Période principale de déroulement du festival"].unique())