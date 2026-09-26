#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
LICENSE: GNU GENERAL PUBLIC LICENSE Version 3, 29 June 2007.
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY.

DESCRIPTION & USAGE:
Translations shared by the PhotoBook scripts. This file is not a script
to run: keep it in the same folder as the other PhotoBook scripts.

The language follows the language of Scribus, or of the system (French
if it is French, English otherwise). To force a language, set LANGUAGE below
to 'en' or 'fr'.
"""
##################################################
# imports
import os, sys, locale, subprocess

LANGUAGE = ''    # '' = follow the system language, or 'en', 'fr'

##################################################
# French translations, keyed by the English text

FRENCH = {
    # common
    'Script failed': 'Échec du script',
    'Error: No document open': 'Erreur : aucun document ouvert',
    'Please, create (or open) a document before running this script ...':
        'Veuillez créer (ou ouvrir) un document avant de lancer ce script...',
    'Please open a Scribus document before running this script.':
        'Veuillez ouvrir un document Scribus avant de lancer ce script.',
    'Warning': 'Attention',
    'Invalid value: {}': 'Valeur invalide : {}',
    'Running script...': 'Exécution du script...',
    'Done.': 'Terminé.',

    # PhotoBookImageCropResize
    'Crop and Resize': 'Recadrer et redimensionner',
    'This script needs the PIL (Pillow) package \n(compatible to your Python version) to be installed.':
        'Ce script nécessite le paquet PIL (Pillow)\n(compatible avec votre version de Python).',
    'Resolution (dpi):': 'Résolution (ppp) :',
    'Color mode:': 'Mode colorimétrique :',
    'File format:': 'Format de fichier :',
    'Resampling:': 'Rééchantillonnage :',
    'CMYK': 'CMJN',
    'B&W': 'N&B',
    'Grey scale': 'Niveaux de gris',
    'Overwrite {}?': 'Écraser {} ?',
    '{}\n will be skipped (processing error).':
        '{}\n sera ignoré (erreur de traitement).',
    'Nothing selected': 'Aucune sélection',
    'Grouped items will be skipped.\nPlease ungroup "{}" and try again.':
        'Les objets groupés seront ignorés.\nVeuillez dégrouper « {} » et réessayer.',

    # PhotoBookLayoutMaker
    'Scribus PhotoBook Layout Maker': 'Scribus PhotoBook - Création de mise en page',
    'This script runs only with Python 3.': 'Ce script ne fonctionne qu\'avec Python 3.',
    'Grouped items are not allowed as source.\nPlease ungroup "{}" and try again.':
        'Les objets groupés ne peuvent pas servir de source.\n'
        'Veuillez dégrouper « {} » et réessayer.',
    'Split/merge rectangle of selected item(s)\nor area within page margins in columns:':
        'Diviser/fusionner le rectangle des objets sélectionnés\n'
        'ou la zone entre les marges de la page en colonnes :',
    '... and rows:': '... et en lignes :',
    'Gap in document units:': 'Espacement en unités du document :',
    'New frame(s) aspect ratio as width:height\n(0:0 = maximum area):':
        'Proportions des nouveaux cadres en largeur:hauteur\n(0:0 = surface maximale) :',
    'New frame(s) scaling in % of selected rectangle:':
        'Taille des nouveaux cadres en % du rectangle sélectionné :',
    'New frame(s) alignment - horizontal:': 'Alignement des nouveaux cadres - horizontal :',
    'New frame(s) alignment - vertical:': 'Alignement des nouveaux cadres - vertical :',
    'Text caption height below image frame in document units\n(0 = no caption):':
        'Hauteur de la légende sous le cadre image en unités du document\n'
        '(0 = pas de légende) :',
    'Remove source items?': 'Supprimer les objets source ?',
    'Alternative border style for new frame(s)?':
        'Style de bordure alternatif pour les nouveaux cadres ?',
    'Save these parameters for future use?':
        'Enregistrer ces paramètres pour les prochaines fois ?',
    '(saved value: {})': '(valeur enregistrée : {})',
    'Yes': 'Oui',
    'No': 'Non',

    # PhotoBookWebGUI
    'Open this address in your browser:': 'Ouvrez cette adresse dans votre navigateur :',

    'Page {} is not empty: clear it first.': 'La page {} n\'est pas vide : effacez-la d\'abord.',
    'Caption': 'Légende',
    'Your text here': 'Votre texte ici',

    # PhotoBookWebGUI.html
    'PhotoBook Web GUI': 'PhotoBook - Livre photo',
    'PhotoBook': 'LivrePhoto',
    'Save': 'Enregistrer',
    'Close': 'Fermer',
    'Closing…': 'Fermeture…',
    'The book is being saved and Scribus is given back. Please wait.':
        'Le livre est en cours d\'enregistrement et Scribus va être rendu. Veuillez patienter.',
    'Closed': 'Fermé',
    'The book is saved.': 'Le livre est enregistré.',
    'You can close this tab and go back to Scribus. Scribus may take a few seconds to redraw the pages.':
        'Vous pouvez fermer cet onglet et revenir à Scribus. Scribus peut mettre quelques secondes '
        'à redessiner les pages.',
    'Not saved yet: choose a file with Save': 'Pas encore enregistré : choisissez un fichier avec Enregistrer',
    'Saving…': 'Enregistrement…',
    'Saved': 'Enregistré',
    'Saved at {}': 'Enregistré à {}',
    'The book is saved in {}': 'Le livre est enregistré dans {}',
    'Rotate left': 'Tourner vers la gauche',
    'Rotate right': 'Tourner vers la droite',
    'Mirror left-right': 'Miroir gauche-droite',
    'Mirror up-down': 'Miroir haut-bas',
    'This image cannot be rotated: no converter (sips or Pillow) found.':
        'Cette image ne peut pas être tournée : aucun convertisseur (sips ou Pillow) trouvé.',
    # images of the book
    'Book images': 'Images du livre',
    'Thumbnails': 'Vignettes',
    'List': 'Liste',
    'Add images…': 'Ajouter des images…',
    'Clear selection': 'Désélectionner',
    'Add the images of your book from your drive.':
        'Ajoutez les images de votre livre depuis votre disque.',
    'Click images to select them for a layout.':
        'Cliquez sur des images pour les sélectionner pour une mise en page.',
    '{} selected for the layout': '{} sélectionnée(s) pour la mise en page',
    'p. {}': 'p. {}',
    'Show large': 'Afficher en grand',
    'Remove from the book': 'Retirer du livre',
    'Add images': 'Ajouter des images',
    'All': 'Toutes',
    'Folders': 'Dossiers',
    'Days': 'Jours',
    'Fold all': 'Tout replier',
    'Unfold all': 'Tout déplier',
    'Select': 'Choisir',
    'Select these images for a layout': 'Sélectionner ces images pour une mise en page',
    'No date': 'Sans date',
    'date of the file': 'date du fichier',
    'Low': 'Faible',
    '{} × {} pixels: {} dpi on a whole page.': '{} × {} pixels : {} ppp sur une page entière.',
    'Good for a whole page.': 'Convient pour une page entière.',
    'Good up to half a page.': 'Convient jusqu\'à une demi-page.',
    'Only for small frames.': 'Seulement pour de petits cadres.',
    'Low resolution: {} dpi in this frame (150 or more recommended).':
        'Résolution faible : {} ppp dans ce cadre (150 ou plus recommandé).',
    'This text was formatted in Scribus (fonts, sizes, colors…): changing it here puts it back in the default style, and that formatting is lost.':
        'Ce texte a été mis en forme dans Scribus (polices, tailles, couleurs…) : le modifier ici le remet '
        'dans le style par défaut, et cette mise en forme est perdue.',
    'Updating the layout will lose the formatting made in Scribus on the texts of this page.':
        'Mettre à jour la mise en page fera perdre la mise en forme faite dans Scribus sur les textes de cette page.',
    'Update anyway': 'Mettre à jour quand même',
    'Parent folder': 'Dossier parent',
    'Select the whole folder': 'Sélectionner tout le dossier',
    'Add to the book': 'Ajouter au livre',
    '{} selected': '{} sélectionnée(s)',
    'No images in this folder.': 'Aucune image dans ce dossier.',
    'already in the book': 'déjà dans le livre',
    'Images added to the book.': 'Images ajoutées au livre.',
    # center
    'Selected images': 'Images sélectionnées',
    'No image selected.': 'Aucune image sélectionnée.',
    'Layouts': 'Mises en page',
    'Layouts for {} images': 'Mises en page pour {} images',
    'More options…': 'Plus d\'options…',
    'Spacing': 'Espacement',
    'Tight': 'Serré',
    'Normal': 'Normal',
    'Airy': 'Aéré',
    'Captions': 'Légendes',
    'Text block': 'Bloc de texte',
    'None': 'Aucun',
    'Top': 'Haut',
    'Bottom': 'Bas',
    'Outer side': 'Côté extérieur',
    'Click a page below to choose where the layout goes.':
        'Cliquez sur une page ci-dessous pour choisir où placer la mise en page.',
    'This page already has content: erase it to make a new layout.':
        'Cette page a déjà un contenu : effacez-le pour faire une nouvelle mise en page.',
    'Select images in the left panel to see the layouts.':
        'Sélectionnez des images dans le panneau de gauche pour voir les mises en page.',
    'No layout for this number of images: create a pattern in More options.':
        'Aucune mise en page pour ce nombre d\'images : créez un modèle dans Plus d\'options.',
    'Choosing a layout replaces the current one.':
        'Choisir une mise en page remplace la mise en page actuelle.',
    'Layout applied.': 'Mise en page appliquée.',
    'Errors:': 'Erreurs :',
    'Page {}': 'Page {}',
    'Pages {}–{}': 'Pages {}–{}',
    'Click a page to choose where the layout goes:':
        'Cliquez sur une page pour choisir où placer la mise en page :',
    'both pages': 'les deux pages',
    'left page': 'page de gauche',
    'right page': 'page de droite',
    'none': 'aucune',
    'Erase page content': 'Effacer le contenu',
    'Erase everything on page {}?': 'Effacer tout le contenu de la page {} ?',
    'Erase everything on pages {}?': 'Effacer tout le contenu des pages {} ?',
    'Erase': 'Effacer',
    'Cancel': 'Annuler',
    'Put this image in the selected frame': 'Mettre cette image dans le cadre sélectionné',
    'Click one of the selected images to put it in the frame, or drag an image onto it.':
        'Cliquez sur une des images sélectionnées pour la mettre dans le cadre, '
        'ou glissez une image dessus.',
    'Zoom': 'Zoom',
    'Fill the frame': 'Remplir le cadre',
    'Drag the image to move it in the frame.': 'Glissez l\'image pour la déplacer dans le cadre.',
    'Undo': 'Annuler',
    'Undo (Ctrl+Z)': 'Annuler (Ctrl+Z)',
    'Undo: {}': 'Annuler : {}',
    'Insert a double page here': 'Insérer une double page ici',
    'double page': 'double page',
    '{} HEIC images converted to JPEG in the folder "PhotoBook JPEG".':
        '{} images HEIC converties en JPEG dans le dossier « PhotoBook JPEG ».',
    'Could not convert: {}': 'Conversion impossible : {}',
    'Done': 'Terminé',
    'Write the caption…': 'Écrivez la légende…',
    'Write your text…': 'Écrivez votre texte…',
    'Emojis are not printed in texts: use the Sticker button for color emojis.':
        'Les émojis ne sont pas imprimés dans les textes : utilisez le bouton Autocollant '
        'pour des émojis en couleur.',
    'The text is too long for the frame: shorten it, or enlarge the frame in Scribus.':
        'Le texte est trop long pour le cadre : raccourcissez-le, ou agrandissez le cadre dans Scribus.',
    'Sticker': 'Autocollant',
    'Add a color emoji on the page': 'Ajouter un émoji en couleur sur la page',
    'Add a sticker': 'Ajouter un autocollant',
    'Click an emoji to put it on the page, then drag it where you want.':
        'Cliquez sur un émoji pour le mettre sur la page, puis faites-le glisser où vous voulez.',
    'Size': 'Taille',
    'Other emoji:': 'Autre émoji :',
    'Add': 'Ajouter',
    'Type or paste any emoji (emoji picker: Ctrl+Cmd+Space on Mac, Windows+. on Windows).':
        'Tapez ou collez n\'importe quel émoji (sélecteur d\'émojis : Ctrl+Cmd+Espace sur Mac, '
        'Windows+. sous Windows).',
    'Type or paste an emoji first.': 'Tapez ou collez d\'abord un émoji.',
    'Delete the sticker': 'Supprimer l\'autocollant',
    'Drag the sticker to move it.': 'Faites glisser l\'autocollant pour le déplacer.',
    # undo steps (PhotoBookWebGUI.py)
    'Move': 'déplacement',
    'Text': 'texte',
    'Rotation': 'rotation',
    'Mirror': 'miroir',
    'Add pages': 'ajout de pages',
    'Insert pages': 'insertion de pages',
    'Move a double page': 'déplacement de double page',
    'Layout': 'mise en page',
    'Image change': 'changement d\'image',
    'Swap images': 'échange d\'images',
    'Crop': 'recadrage',
    # pages
    'Pages': 'Pages',
    'This document has single pages, not double pages.':
        'Ce document a des pages simples, pas des doubles pages.',
    'To get double pages, close this page, then in Scribus choose File > Document Setup, tick Double Sided with the first page on the right, and run the script again. Or close the document in Scribus and create the book from this page.':
        'Pour avoir des doubles pages, fermez cette page, puis dans Scribus choisissez Fichier > Réglages '
        'du document, cochez Pages en vis-à-vis avec la première page à droite, et relancez le script. '
        'Ou fermez le document dans Scribus et créez le livre depuis cette page.',
    '+ 1 page': '+ 1 page',
    '+ 2 pages': '+ 2 pages',
    'New photo book': 'Nouveau livre photo',
    'No document is open in Scribus: choose the size of the pages.':
        'Aucun document n\'est ouvert dans Scribus : choisissez la taille des pages.',
    'Unit': 'Unité',
    'Page width': 'Largeur de page',
    'Page height': 'Hauteur de page',
    'Margins': 'Marges',
    'Bleed': 'Fond perdu',
    'The first page is alone on the right, the next ones are double pages.':
        'La première page est seule à droite, les suivantes sont des doubles pages.',
    'Create the book': 'Créer le livre',
    'Save the book': 'Enregistrer le livre',
    'File': 'Fichier',
    'The book has changes that are not saved.':
        'Le livre a des modifications qui ne sont pas enregistrées.',
    'Close without saving': 'Fermer sans enregistrer',
    'Save and close': 'Enregistrer et fermer',
    # options
    'Layout options': 'Options de mise en page',
    'Gap': 'Espacement',
    'Caption height (mm)': 'Hauteur des légendes (mm)',
    'Text block size (%)': 'Taille du bloc de texte (%)',
    'Scaling (%)': 'Taille (%)',
    'Frame aspect ratio (0 = free)': 'Proportions des cadres (0 = libre)',
    'Horizontal alignment': 'Alignement horizontal',
    'Vertical alignment': 'Alignement vertical',
    'Left': 'Gauche',
    'Center': 'Centre',
    'Right': 'Droite',
    'Frame border': 'Bordure des cadres',
    'Dark grey': 'Gris foncé',
    'White': 'Blanc',
    'My patterns': 'Mes modèles',
    'None yet.': 'Aucun pour l\'instant.',
    'Delete': 'Supprimer',
    'New pattern': 'Nouveau modèle',
    'Columns': 'Colonnes',
    'Rows': 'Lignes',
    'Drag over cells to merge them, click a merged cell to split it.':
        'Glissez sur des cases pour les fusionner, cliquez sur une case fusionnée pour la diviser.',
    'Save to my patterns': 'Enregistrer dans mes modèles',
    'This pattern is already in the list.': 'Ce modèle est déjà dans la liste.',
    'Pattern saved.': 'Modèle enregistré.',
    'Save settings as default': 'Enregistrer ces réglages par défaut',
    'Settings saved.': 'Réglages enregistrés.',
}

TRANSLATIONS = {'fr': FRENCH}

##################################################
# language detection

def systemLanguages():
    """ Language codes of Scribus and of the system, most relevant first."""
    languages = []
    try:
        import scribus
        languages.append(scribus.getGuiLanguage())
    except Exception:
        pass
    if sys.platform == 'darwin':
        # applications started from the Finder have no LANG variable
        try:
            output = subprocess.run(['defaults', 'read', '-g', 'AppleLanguages'],
                capture_output=True, text=True, timeout=2).stdout
            languages += [l.strip(' \t"(),') for l in output.splitlines()]
        except Exception:
            pass
    for variable in ('LANGUAGE', 'LC_ALL', 'LC_MESSAGES', 'LANG'):
        languages += os.environ.get(variable, '').split(':')
    try:
        languages.append(locale.getlocale()[0] or '')
    except Exception:
        pass
    return [l for l in languages if l and l not in ('C', 'POSIX')]

def detectLanguage():
    """ Two-letter code of the language to use ('en' if not translated)."""
    if LANGUAGE:
        return LANGUAGE
    for language in systemLanguages():
        code = language[:2].lower()
        if code == 'en' or code in TRANSLATIONS:
            return code
    return 'en'

CURRENT = TRANSLATIONS.get(detectLanguage(), {})

def tr(text):
    """ Translate an English text to the current language."""
    return CURRENT.get(text, text)
