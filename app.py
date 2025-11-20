import streamlit as st
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image
import re
import io

# Configuration de la page
st.set_page_config(page_title="Extracteur Lambert 2 (OCR)", layout="centered")

st.title("📍 Extracteur Lambert 2 (Mode OCR)")
st.info("ℹ️ Ce mode utilise la reconnaissance visuelle (OCR). C'est plus lent mais beaucoup plus puissant pour les documents scannés.")

# 1. Upload du fichier
uploaded_file = st.file_uploader("Choisissez votre fichier PDF", type="pdf")

if uploaded_file is not None:
    # Lire le fichier en binaire
    pdf_bytes = uploaded_file.getvalue()
    
    # On utilise pdf2image pour compter les pages rapidement sans tout convertir d'un coup
    # (Une petite astuce pour avoir le nombre de pages sans surcharger la mémoire)
    try:
        info = convert_from_bytes(pdf_bytes, first_page=1, last_page=1)
        # Malheureusement pdf2image ne donne pas le total facilement sans tout charger
        # On va demander à l'utilisateur ou mettre une limite par défaut, 
        # ou utiliser une méthode légère pour compter.
        # Pour simplifier ici, on charge la première page pour valider le PDF.
        st.success("Fichier chargé. Prêt pour l'analyse.")
    except Exception as e:
        st.error(f"Erreur de lecture du PDF : {e}")

    # 2. Paramètres
    st.subheader("Paramètres d'extraction")
    col1, col2 = st.columns(2)
    with col1:
        start_page = st.number_input("Page de début", min_value=1, value=1)
    with col2:
        # On met une valeur arbitraire haute par défaut, le code s'arrêtera à la fin du PDF
        end_page = st.number_input("Page de fin (estimation)", min_value=1, value=30)

    if st.button("Lancer l'analyse OCR"):
        results = []
        logs = []
        
        # Barre de progression
        progress_text = "Démarrage de l'OCR... (cela peut prendre quelques secondes par page)"
        my_bar = st.progress(0, text=progress_text)
        
        # Regex très flexible pour l'OCR (tolère les fautes de lecture comme 'etendu' sans accent)
        # On cherche : "Lambert" ... un "2" ... un ":" ... (nombre X) ... (nombre Y)
        regex_pattern = r"Lambert.*?2.*?:?\s*([0-9]{6,7}[.,]?[0-9]*).*?([0-9]{7}[.,]?[0-9]*)"

        # On boucle sur les pages demandées
        for i in range(start_page, end_page + 1):
            try:
                # Conversion PDF -> Image (une seule page à la fois pour économiser la RAM)
                # dpi=300 assure une bonne qualité de lecture
                images = convert_from_bytes(pdf_bytes, first_page=i, last_page=i, fmt='jpeg', dpi=300)
                
                if not images:
                    break # Fin du document atteinte
                
                page_image = images[0]
                
                # OPTIMISATION : On ne rogne que la partie GAUCHE de l'image (30% de la largeur)
                # Cela accélère l'OCR et réduit les erreurs en ignorant le plan à droite.
                width, height = page_image.size
                left_area = (0, 0, width * 0.35, height) # Crop: Gauche, Haut, Droite, Bas
                cropped_image = page_image.crop(left_area)
                
                # Extraction du texte via Tesseract
                # config='--psm 6' assume un bloc de texte uniforme
                text = pytesseract.image_to_string(cropped_image, lang='fra', config='--psm 6')
                
                # Nettoyage basique (remplacer les virgules par des points pour les décimales si besoin)
                text_clean = text.replace('\n', ' ') # Mettre sur une ligne pour aider le regex
                
                # Recherche
                matches = re.findall(regex_pattern, text_clean, re.IGNORECASE)
                
                if matches:
                    for match in matches:
                        # On nettoie les nombres (parfois l'OCR met des virgules au lieu de points)
                        x = match[0].replace(',', '.')
                        y = match[1].replace(',', '.')
                        
                        results.append(f"{x},{y}")
                        logs.append(f"Page {i}: ✅ Trouvé -> {x}, {y}")
                else:
                    # Debug : afficher un bout de ce que l'OCR a vu pour comprendre
                    excerpt = text_clean[:100].replace('\n', '') 
                    logs.append(f"Page {i}: ❌ Rien trouvé. (OCR a vu: '{excerpt}...')")

                # Mise à jour barre
                my_bar.progress((i - start_page + 1) / (end_page - start_page + 1), text=f"Traitement page {i}...")
                
            except Exception as e:
                logs.append(f"Page {i}: Erreur ou fin du document ({str(e)})")
                break

        my_bar.empty()

        # 3. Résultats
        st.divider()
        if results:
            st.success(f"Extraction terminée ! {len(results)} coordonnées trouvées.")
            txt_output = "\n".join(results)
            
            with st.expander("Voir les résultats"):
                st.text(txt_output)
            
            st.download_button(
                label="📥 Télécharger le fichier texte",
                data=txt_output,
                file_name="coordonnees_lambert_ocr.txt",
                mime="text/plain"
            )
        else:
            st.warning("Aucune coordonnée trouvée.")

        with st.expander("Journal détaillé (Logs)"):
            for log in logs:
                st.write(log)
