"""
Utilitaire pour extraire le texte de différents formats de fichiers
"""

import logging
from io import BytesIO
from typing import Optional

logger = logging.getLogger(__name__)


def extract_text_from_file(file_content: bytes, filename: str) -> Optional[str]:
    """
    Extrait le texte d'un fichier en fonction de son extension.

    Args:
        file_content: Contenu du fichier en bytes
        filename: Nom du fichier avec extension

    Returns:
        Le texte extrait ou None en cas d'erreur
    """
    extension = filename.lower().split('.')[-1] if '.' in filename else ''

    try:
        if extension == 'pdf':
            return extract_text_from_pdf(file_content)
        elif extension in ['docx']:
            return extract_text_from_docx(file_content)
        elif extension in ['txt', 'md']:
            return extract_text_from_text(file_content)
        else:
            logger.warning(f"Format de fichier non supporté: {extension}")
            # Essayer de lire comme du texte simple
            return extract_text_from_text(file_content)
    except Exception as e:
        logger.error(f"Erreur lors de l'extraction du texte de {filename}: {e}")
        return None


def extract_text_from_pdf(file_content: bytes) -> str:
    """Extrait le texte d'un fichier PDF."""
    try:
        from PyPDF2 import PdfReader

        pdf_file = BytesIO(file_content)
        reader = PdfReader(pdf_file)

        text_parts = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)

        full_text = '\n\n'.join(text_parts)

        # Nettoyer le texte
        full_text = clean_extracted_text(full_text)

        return full_text
    except Exception as e:
        logger.error(f"Erreur lors de l'extraction du PDF: {e}")
        raise


def extract_text_from_docx(file_content: bytes) -> str:
    """Extrait le texte d'un fichier DOCX."""
    try:
        from docx import Document

        docx_file = BytesIO(file_content)
        doc = Document(docx_file)

        text_parts = []

        # Extraire le texte des paragraphes
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text_parts.append(paragraph.text)

        # Extraire le texte des tableaux
        for table in doc.tables:
            for row in table.rows:
                row_text = []
                for cell in row.cells:
                    if cell.text.strip():
                        row_text.append(cell.text.strip())
                if row_text:
                    text_parts.append(' | '.join(row_text))

        full_text = '\n'.join(text_parts)

        # Nettoyer le texte
        full_text = clean_extracted_text(full_text)

        return full_text
    except Exception as e:
        logger.error(f"Erreur lors de l'extraction du DOCX: {e}")
        raise


def extract_text_from_text(file_content: bytes) -> str:
    """Extrait le texte d'un fichier texte simple."""
    try:
        # Essayer différents encodages
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']

        for encoding in encodings:
            try:
                text = file_content.decode(encoding)
                return clean_extracted_text(text)
            except UnicodeDecodeError:
                continue

        # Si aucun encodage ne fonctionne, utiliser utf-8 avec ignore
        text = file_content.decode('utf-8', errors='ignore')
        return clean_extracted_text(text)
    except Exception as e:
        logger.error(f"Erreur lors de l'extraction du texte: {e}")
        raise


def clean_extracted_text(text: str) -> str:
    """
    Nettoie le texte extrait en supprimant les caractères indésirables
    et en normalisant les espaces.
    """
    if not text:
        return ""

    # Remplacer les multiples espaces par un seul
    import re
    text = re.sub(r'\s+', ' ', text)

    # Remplacer les multiples sauts de ligne par deux
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)

    # Supprimer les espaces en début et fin
    text = text.strip()

    return text
