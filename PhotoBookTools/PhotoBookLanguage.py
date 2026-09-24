#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
LICENSE: GNU GENERAL PUBLIC LICENSE Version 3, 29 June 2007.
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY.

DESCRIPTION & USAGE:
Translations shared by the PhotoBook scripts. This file is not a script
to run: keep it in the same folder as the other PhotoBook scripts.

The language follows the system language (French if the system is in
French, English otherwise). To force a language, set LANGUAGE below
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
    'Yes': 'Oui',
    'No': 'Non',
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
    'Left': 'Gauche',
    'Center': 'Centre',
    'Right': 'Droite',
    'Top': 'Haut',
    'Bottom': 'Bas',
    'Text caption height below image frame in document units\n(0 = no caption):':
        'Hauteur de la légende sous le cadre image en unités du document\n'
        '(0 = pas de légende) :',
    'Remove source items?': 'Supprimer les objets source ?',
    'Alternative border style for new frame(s)?':
        'Style de bordure alternatif pour les nouveaux cadres ?',
    'Save these parameters for future use?':
        'Enregistrer ces paramètres pour les prochaines fois ?',
    '(saved value: {})': '(valeur enregistrée : {})',
}

TRANSLATIONS = {'fr': FRENCH}

##################################################
# language detection

def systemLanguages():
    """ Language codes of the system, most relevant first."""
    languages = []
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
