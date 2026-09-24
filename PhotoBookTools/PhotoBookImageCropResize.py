#! /usr/bin/env python
#-*- coding: utf-8 -*-
'''
VERSION: 1.0 of 2021-07-31
AUTHOR: Rafferty River. 
LICENSE: GNU GENERAL PUBLIC LICENSE Version 3, 29 June 2007. 
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY.

DESCRIPTION & USAGE:
This script loops over every selected object, and for all image
frames that are not empty, it will crop and resize a COPY of
the image file and add the suffix "_cropped" to it.

This is a reworked version of an old Scribus script 
'Image_crop_resize_and_color_conversion_GUI.py' of 
prof. MS. José Antonio Meira da Rocha of 2011-01-05a with
License GPL.

IMPORTANT REMARK: this script needs the Pillow (PIL) package
to be installed in (Scribus) Python (https://python-pillow.org).
'''
##################################################
# imports
import sys, os

try:
    from scribus import *
except ImportError:
    scribus.messageBox("Script failed",
        "This Python script can only be run from within Scribus.",
        scribus.ICON_WARNING,scribus.BUTTON_OK)
    sys.exit(1)

# translations (PhotoBookLanguage.py must be in the same folder)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PhotoBookLanguage import tr

try:
    # if PIL-package installed but not found, uncomment one of following lines:
    #sys.path.append('C:\\Users\\Python37\\Lib\\site-packages')  # Windows
    #sys.path.append('/usr/lib/python3/dist-packages')   # Linux
    from PIL import Image
except ImportError:
    scribus.messageBox(tr("Script failed"),
        tr("This script needs the PIL (Pillow) package \n"
        "(compatible to your Python version) to be installed."),
        scribus.ICON_CRITICAL,scribus.BUTTON_OK)
    sys.exit(1)
    
##################################################
class ScPhotoBookImageCropResize:
    """ PhotoBookImageCropResize itself."""

    def __init__(self, resolution='300', mode='RGB', fileFormat='.jpg', resample='BICUBIC'):
        """ Setup basic things """
        self.resolution = resolution
        if mode == 'B&W':
            self.mode = '1'
        elif mode == 'Grey scale':
            self.mode = 'L'
        else:
            self.mode = mode
        self.fileFormat = fileFormat
        self.resample = resample

    def handleImage(self, imageFrame):
        """ Crop, resize, convert and save Image function."""
        imgFile = scribus.getImageFile(imageFrame)
        try:
            image = Image.open(imgFile)
            # Calculate DPI
            unit = scribus.getUnit()
            scribus.setUnit(UNIT_INCHES)
            imageResolution = int(self.resolution)
            frameSizeX,frameSizeY = scribus.getSize(imageFrame)
            newWidth = int(frameSizeX * imageResolution)
            newHeight = int(frameSizeY * imageResolution)
            scribus.setUnit(UNIT_POINTS)

            # Calculate cropping
            imageXOffset = scribus.getProperty(imageFrame,'imageXOffset')
            imageYOffset = scribus.getProperty(imageFrame,'imageYOffset')
            frameSizeX,frameSizeY = scribus.getSize(imageFrame)
            imageXScale = scribus.getProperty(imageFrame,'imageXScale')
            imageYScale = scribus.getProperty(imageFrame,'imageYScale')
            imageSizeX, imageSizeY = image.size

            # calculate crop box
            left = int(imageXOffset * -1)
            top = int(imageYOffset * -1)
            right = int(left + (frameSizeX / imageXScale))
            bottom = int(top + (frameSizeY / imageYScale))
        
            # Limit crop to image area 
            # (avoid black areas due to crop bigger than image)
            if right > imageSizeX: 
                right = imageSizeX
            if bottom > imageSizeY: 
                bottom = imageSizeY
            if imageXOffset > 0: 
                left = 0
            if imageYOffset > 0: 
                top = 0
        
            # Recalculate new image dimensions
            # to fit proportionaly
            proportionX = newWidth / (right-left)
            proportionY = newHeight / (bottom-top)
            if proportionX > proportionY:
                newHeight = int(newWidth * (bottom-top) /(right-left))
            else:
                newWidth = int(newHeight * (right-left) / (bottom-top))

            # Cropping
            newImage = image.crop((left,top,right,bottom))
        
            # Resize
            if self.resample == 'BICUBIC':
                newImage = newImage.resize((newWidth,newHeight),Image.BICUBIC)
            elif self.resample == 'LANCZOS':
                newImage = newImage.resize((newWidth,newHeight),Image.LANCZOS)
            else:
                newImage = newImage.resize((newWidth,newHeight),Image.BILINEAR)
        
            # Color space conversion
            if newImage.mode != self.mode:
                newImage = newImage.convert(self.mode)

            # Save new image with suffix '_cropped'
            scribus.setUnit(unit)  # restore original document unit
            name,ext = os.path.splitext(imgFile)
            newImageFile = (name + '_cropped'+ self.fileFormat)
            if os.path.exists(newImageFile):
                overwrite = scribus.messageBox(tr('Warning'), tr('Overwrite {}?').format(newImageFile),
                    ICON_WARNING, button2=scribus.BUTTON_NO, button1=scribus.BUTTON_YES)
                if int(overwrite) > 16384:  # BUTTON_NO was clicked
                    return
            newImage.save(newImageFile, dpi=(imageResolution,imageResolution))

            # Reload new image in image frame
            scribus.loadImage(newImageFile,imageFrame)
            
        except:
            scribus.messageBox(tr('Warning'),
                tr('{}\n will be skipped (processing error).').format(imgFile),
                ICON_WARNING, BUTTON_OK)
        return
        
    def handleSelection(self):
        """ Handle selected frames."""
        selectionList = []
        nbrSelected = scribus.selectionCount()
        scribus.progressTotal(nbrSelected)
        if nbrSelected == 0:
            scribus.messageBox(tr('Warning'), tr('Nothing selected'), ICON_WARNING)
        else:    # one or more items selected
            for i in range (0, selectionCount()):
                scribus.progressSet(i)
                obj = getSelectedObject(i)
                selectionList.append(obj)
                objectType = getObjectType(obj)
                if objectType == 'Group':
                    messageBox(tr('Warning'), tr('Grouped items will be skipped.\n'
                        'Please ungroup "{}" and try again.').format(obj), ICON_WARNING)
                elif (objectType == 'ImageFrame') and (getImageFile(obj) != ""):
                    self.handleImage(obj)
                else: # not an image frame -> skip
                    pass
        return

##################################################
# User interface (Scribus built-in dialogs, no Tkinter needed)

TITLE = tr('Crop and Resize')

def askChoice(message, default, choices=None, validate=None):
    """ Ask a value with scribus.valueDialog until it is valid.
        Returns None if the user cancelled (empty answer)."""
    value = default
    while True:
        prompt = tr(message)
        if choices:
            prompt += '\n(' + ', '.join(tr(c) for c in choices) + ')'
            value = tr(value)
        value = scribus.valueDialog(TITLE, prompt, value).strip()
        if value == '':
            return None
        if choices:
            # accept the translated or the English name
            for choice in choices:
                if value.lower() in (choice.lower(), tr(choice).lower()):
                    return choice
        elif validate is None or validate(value):
            return value
        scribus.messageBox(TITLE, tr('Invalid value: {}').format(value), ICON_WARNING)

def askOptions():
    """ Ask all options. Returns None if the user cancelled."""
    resolution = askChoice('Resolution (dpi):', '300',
        validate=lambda v: v.isdigit() and int(v) > 0)
    if resolution is None:
        return None
    mode = askChoice('Color mode:', 'RGB', ['RGB','CMYK','B&W','Grey scale'])
    if mode is None:
        return None
    fileFormat = askChoice('File format:', '.jpg', ['.jpg','.png','.tif'])
    if fileFormat is None:
        return None
    resample = askChoice('Resampling:', 'BICUBIC', ['BICUBIC','BILINEAR','LANCZOS'])
    if resample is None:
        return None
    return resolution, mode, fileFormat, resample

##################################################
# Start program

def main():
    if scribus.haveDoc() == 0:
        scribus.messageBox(tr("Script failed"),
            tr("Please open a Scribus document before running this script."),
            scribus.ICON_WARNING,scribus.BUTTON_OK)
        return
    
    try:
        scribus.statusMessage(tr('Running script...'))
        scribus.progressReset()
        unit = scribus.getUnit()
        options = askOptions()
        if options is not None:
            ScPhotoBookImageCropResize(*options).handleSelection()
    finally:
        if scribus.haveDoc():
            scribus.redrawAll()
        scribus.setUnit(unit)
        scribus.statusMessage(tr('Done.'))
        scribus.progressReset()

if __name__ == '__main__':
    main()
