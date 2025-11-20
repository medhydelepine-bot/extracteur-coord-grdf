import streamlit as st
import pdfplumber
import re
from io import BytesIO

# Configuration de la page
st.set_page_config(page_title="Extracteur Lambert 2", layout="centered")

st.title("📍 Extracteur de Coordonnées Lambert 2")
st.markdown("""
Cette application lit un PDF, cherche les coordonnées au format :
**Lambert 2 étendu: X m,Y m,L2E** et génère un fichier CSV/Texte prêt à l'emploi.
""")

# 1. Upload du fichier
uploaded_file = st.file_uploader("Choisissez votre fichier PDF", type="pdf")

if uploaded_file is not None:
    # On ouvre le PDF pour compter les pages
    with pdfplumber.open(uploaded_file) as pdf:
        total_pages = len(pdf.pages)
        st.success(f"Fichier chargé avec succès ! ({total_pages} pages)")

        # 2. Sélection de la plage de pages
        st.subheader("Paramètres d'extraction")
        col1, col2 = st.columns(2)
        with col1:
            start_page = st.number_input("Page de début", min_value=1, max_value=total_pages, value=1)
        with col2:
            end_page = st.number_input("Page de fin", min_value=1, max_value=total_pages, value=total_pages)

        # Bouton pour lancer le traitement
        if st.button("Extraire les coordonnées"):
            results = []
            logs = []
            
            # Barre de progression
            progress_bar = st.progress(0)
            
            # Le motif (Regex) basé sur votre image
            # Explication : On cherche "Lambert 2 étendu:", des espaces, un nombre (X), " m,", un nombre (Y)
  # Nouveau motif plus robuste (ignore les accents et gère mieux les sauts de ligne)
            # Explication : On cherche "Lambert 2", puis n'importe quels caractères jusqu'au ":", 
            # puis le nombre X, puis le séparateur (avec ou sans 'm'), puis le nombre Y.
            regex_pattern = r"Lambert\s+2.*:\s*([0-9.]+)\s*(?:m|)\s*,\s*([0-9.]+)"
            # Boucle sur les pages sélectionnées
            # On fait range(start-1, end) car les pages commencent à 0 dans le code mais à 1 pour l'humain
            pages_to_process = range(start_page - 1, end_page)
            
            for i, page_num in enumerate(pages_to_process):
                page = pdf.pages[page_num]
                
                # On se concentre sur la partie gauche/centrale (optionnel, mais aide à la précision)
                # width = page.width
                # height = page.height
                # crop_box = (0, 0, width * 0.7, height) # On ne regarde que les 70% gauche
                # cropped_page = page.crop(crop_box)
                # text = cropped_page.extract_text()
                
                # Pour l'instant, on lit toute la page car le label est très spécifique
                text = page.extract_text()
                
                if text:
                    matches = re.findall(regex_pattern, text)
                    if matches:
                        for match in matches:
                            x_coord = match[0]
                            y_coord = match[1]
                            # Ajout au format demandé : X,Y
                            results.append(f"{x_coord},{y_coord}")
                            logs.append(f"Page {page_num + 1}: Trouvé -> {x_coord}, {y_coord}")
                    else:
                        logs.append(f"Page {page_num + 1}: Aucune coordonnée trouvée.")
                
                # Mise à jour barre de progression
                progress_bar.progress((i + 1) / len(pages_to_process))

            # 3. Affichage et Téléchargement
            st.divider()
            if results:
                st.success(f"{len(results)} coordonnées extraites !")
                
                # Création du contenu du fichier texte
                txt_output = "\n".join(results)
                
                # Aperçu des données
                with st.expander("Voir les données extraites"):
                    st.text(txt_output)
                
                # Bouton de téléchargement
                st.download_button(
                    label="📥 Télécharger le fichier texte (X,Y)",
                    data=txt_output,
                    file_name="coordonnees_lambert.txt",
                    mime="text/plain"
                )
            else:
                st.warning("Aucune coordonnée correspondant au format n'a été trouvée dans les pages sélectionnées.")
            
            # Logs techniques (pour vérifier)
            with st.expander("Voir le journal de traitement"):
                for log in logs:

                    st.write(log)
