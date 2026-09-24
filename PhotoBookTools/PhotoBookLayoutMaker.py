#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
VERSION: 1.0 of 2021-07-31
AUTHOR: Rafferty River. 
LICENSE: GNU GENERAL PUBLIC LICENSE Version 3, 29 June 2007. 
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY.

DESCRIPTION & USAGE:
(tested on Scribus 1.5.6+ with Python 3 on Windows 10 and Linux).

PhotoBookLayoutMaker is a script for creating Image Frames in Scribus in
a fast and flexible way. Many options are available in the interface.
"""
##################################################
# imports
import sys,  platform, os
from configparser import ConfigParser

try:
    from scribus import *
except ImportError:
    print("This Python script is written for the Scribus \
      scripting interface.")
    print("It can only be run from within Scribus.")
    sys.exit(1)

# translations (PhotoBookLanguage.py must be in the same folder)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PhotoBookLanguage import tr

python_version = platform.python_version()
if python_version[0:1] != "3":
    print("This script runs only with Python 3.")
    messageBox(tr("Script failed"),
        tr("This script runs only with Python 3."),
        ICON_CRITICAL)	
    sys.exit(1)

##################################################
class ScPhotoBookLayoutMaker:
    """ PhotoBookLayoutMaker itself."""

    def __init__(self, cols=0, rows=0, gap=0.0, aspectratio=0, scale=0.0,
        alignh="", alignv="", captionh=0.0, removeframe=1, alternateborder=0):
        """ Setup basic things """
        # params
        self.cols = cols
        self.rows = rows
        self.gap = gap
        self.aspectratio = aspectratio
        self.scale = scale / 100
        self.alignh = alignh
        self.alignv = alignv
        self.captionh = captionh
        self.removeframe = removeframe
        self.alternateborder = alternateborder        
        defineColorCMYK("frameFillColor", 0, 0, 0, 64) # default is Light Grey

        # create 2 frame border styles (line width is measured in points)
        defineColorCMYK("frameBorderColor1", 0, 0, 0, 200) # default is Dark Grey
        self.frameBorderLineStyle1 = "frameBorderLineStyle1"
        createCustomLineStyle(self.frameBorderLineStyle1, [
            {
                'Color': "frameBorderColor1",
                'Width': 1
            }
        ]);
        defineColorCMYK("frameBorderColor2", 0, 0, 0, 0) # default is White
        self.frameBorderLineStyle2 = "frameBorderLineStyle2"
        createCustomLineStyle(self.frameBorderLineStyle2, [
            {
                'Color': "frameBorderColor2",
                'Width': 1
            }
        ]);

        # create character and paragraph style for caption text (if needed)
        if self.captionh != 0:
            unit = [pt, mm, inch, p, cm, c]   # Scribus units
            self.cStyleCaption = "characterStyleCaptionText"
            scribus.createCharStyle(name=self.cStyleCaption,
                fontsize=abs(self.captionh / unit[getUnit()]) // 1.5)
            self.pStyleCaption = "paragraphStyleCaptionText"
            scribus.createParagraphStyle(name=self.pStyleCaption, linespacingmode=0,
                alignment=ALIGN_CENTERED, charstyle=self.cStyleCaption)

    def createLayout(self):
        """ Draw image frame(s) within a rectangular selection or within page margins."""

        # current page measures
        pageWidth, pageHeight = getPageNSize(currentPage())
        marginTop, marginLeft, marginRight, marginBottom = getPageNMargins(currentPage())

        # source frame measures
        selectionList = []
        nbrSelected = scribus.selectionCount()
        if nbrSelected == 0:    # nothing selected: select area within page margins
            frameX = marginLeft
            frameY = marginTop
            frameWidth = pageWidth - marginLeft - marginRight
            frameHeight = pageHeight - marginTop - marginBottom
        else:    # one or more items selected
            for i in range (0, nbrSelected):
                obj = getSelectedObject(i)
                selectionList.append(obj)
                if getObjectType(obj) == 'Group':
                    messageBox(tr('Warning'), tr('Grouped items are not allowed as source.\n'
                        'Please ungroup "{}" and try again.').format(obj), ICON_CRITICAL)
                    sys.exit(1)
                frameX, frameY = getPosition(obj)
                frameWidth, frameHeight = getSize(obj)
                if i == 0:
                    posXmin, posYmin = getPosition(obj)
                    posXmax = posXmin + frameWidth
                    posYmax = posYmin + frameHeight                 
                else:
                    if frameX < posXmin:
                        posXmin = frameX
                    if frameY < posYmin:
                        posYmin = frameY
                    if frameX + frameWidth > posXmax:
                        posXmax = frameX + frameWidth
                    if frameY + frameHeight > posYmax:
                        posYmax = frameY + frameHeight
            frameX = posXmin
            frameY = posYmin
            frameWidth = posXmax - posXmin
            frameHeight = posYmax - posYmin

        # generated frame(s) measures
        newFrameW = (self.scale * frameWidth - (self.gap * (self.cols - 1))) / self.cols
        if self.captionh > 0:
            newFrameH = (self.scale * frameHeight - self.gap * (self.rows - 1) - self.captionh * self.rows) / self.rows
        else:
            newFrameH = (self.scale * frameHeight - (self.gap * (self.rows - 1))) / self.rows
        newAspectR = newFrameW / newFrameH

        # aspect ratio
        if self.aspectratio == 0.0:
            pass
        else:
            if self.aspectratio < newAspectR:
                newFrameW = newFrameH * self.aspectratio
            else:
                newFrameH = newFrameW / self.aspectratio

        # alignment
        if self.alignh == "Center":
            offsetX =  frameX + (frameWidth - newFrameW * self.cols - self.gap * (self.cols - 1))/2
        elif self.alignh == "Right":
            offsetX =  frameX + frameWidth - newFrameW * self.cols - self.gap * (self.cols - 1)
        else:
            offsetX = frameX
        if self.alignv == "Center":
            if self.captionh > 0:
                offsetY =  frameY + (frameHeight - (newFrameH + self.captionh) * self.rows - self.gap * (self.rows - 1))/2
            else:
                offsetY =  frameY + (frameHeight - newFrameH * self.rows - self.gap * (self.rows - 1))/2
        elif self.alignv == "Bottom":
            if self.captionh > 0:
                offsetY =  frameY + frameHeight - (newFrameH + self.captionh) * self.rows - self.gap * (self.rows - 1)
            else:
                offsetY =  frameY + frameHeight - newFrameH * self.rows - self.gap * (self.rows - 1)
        else:
            offsetY = frameY

        # border style
        if self.alternateborder:
            frameBorderLineStyle = self.frameBorderLineStyle2
        else:
            frameBorderLineStyle = self.frameBorderLineStyle1

        # draw the frames
        for i in range (1,  self.cols + 1):
            resetY = offsetY
            for j in range (1, self.rows + 1):
                newFrame = createImage(offsetX, offsetY, newFrameW, newFrameH)
                setFillColor("frameFillColor", newFrame)
                setCustomLineStyle(frameBorderLineStyle, newFrame)
                # draw caption text (if needed):
                if self.captionh != 0:
                    if self.captionh > 0:
                        captionTxt = createText(offsetX, offsetY + newFrameH, newFrameW, self.captionh)
                        offsetY = offsetY + self.captionh
                    else:    #self.captionh < 0
                        captionTxt = createText(offsetX, offsetY + newFrameH + self.captionh,
                            newFrameW, - self.captionh)
                    setText(newFrame, captionTxt)
                    selectObject(captionTxt)
                    setParagraphStyle(self.pStyleCaption, captionTxt)
                    setTextVerticalAlignment(ALIGNV_CENTERED, captionTxt)
                offsetY = offsetY + self.gap + newFrameH
            offsetX = offsetX + self.gap + newFrameW
            j = 1
            offsetY = resetY

        # remove source items
        if self.removeframe:
            for i in range (0, len(selectionList)):
                deleteObject(selectionList[i])
        else:
            pass

        return None

##################################################
# User interface (Scribus built-in dialogs, no Tkinter needed)

TITLE = tr('Scribus PhotoBook Layout Maker')

def isFloat(value):
    try:
        float(value)
        return True
    except ValueError:
        return False

def askValue(message, default, choices=None, validate=None):
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

def askYesNo(message, default):
    """ Ask a yes/no question. Returns 1 for yes, 0 for no."""
    message = (tr(message) + '\n'
        + tr('(saved value: {})').format(tr('Yes') if default == '1' else tr('No')))
    answer = scribus.messageBox(TITLE, message, ICON_NONE,
        button1=scribus.BUTTON_YES, button2=scribus.BUTTON_NO)
    return 1 if int(answer) == scribus.BUTTON_YES else 0

def askParameters():
    """ Ask all parameters, starting from the values saved in
        'PhotoBookLayoutMaker.cfg'. Returns None if the user cancelled."""
    configFile = os.path.join(os.path.dirname(__file__), 'PhotoBookLayoutMaker.cfg')
    config = ConfigParser()
    config.read(configFile)
    cfg = config['DEFAULT']

    isPositiveInt = lambda v: v.isdigit() and int(v) > 0

    cols = askValue('Split/merge rectangle of selected item(s)\n'
        'or area within page margins in columns:', cfg.get('cols', '2'),
        validate=isPositiveInt)
    if cols is None:
        return None
    rows = askValue('... and rows:', cfg.get('rows', '1'), validate=isPositiveInt)
    if rows is None:
        return None
    gap = askValue('Gap in document units:', cfg.get('gap', '5.0'), validate=isFloat)
    if gap is None:
        return None
    aspect = askValue('New frame(s) aspect ratio as width:height\n(0:0 = maximum area):',
        cfg.get('aspectwidth', '0') + ':' + cfg.get('aspectheight', '0'),
        validate=lambda v: len(v.split(':')) == 2
            and all(x.strip().isdigit() for x in v.split(':')))
    if aspect is None:
        return None
    aspectwidth, aspectheight = [x.strip() for x in aspect.split(':')]
    scale = askValue('New frame(s) scaling in % of selected rectangle:',
        cfg.get('scale', '100.0'), validate=lambda v: isFloat(v) and float(v) > 0)
    if scale is None:
        return None
    alignh = askValue('New frame(s) alignment - horizontal:', cfg.get('alignh', 'Center'),
        ['Left', 'Center', 'Right'])
    if alignh is None:
        return None
    alignv = askValue('New frame(s) alignment - vertical:', cfg.get('alignv', 'Center'),
        ['Top', 'Center', 'Bottom'])
    if alignv is None:
        return None
    savedCaptionh = cfg.get('captionh', '5.0')
    captionh = askValue('Text caption height below image frame in document units\n'
        '(0 = no caption):',
        savedCaptionh if cfg.get('caption', '0') == '1' else '0', validate=isFloat)
    if captionh is None:
        return None
    caption = 0 if float(captionh) == 0 else 1
    removeframe = askYesNo('Remove source items?', cfg.get('removeframe', '1'))
    alternateborder = askYesNo('Alternative border style for new frame(s)?',
        cfg.get('alternateborder', '0'))

    if askYesNo('Save these parameters for future use?', '0'):
        cfg['cols'] = cols
        cfg['rows'] = rows
        cfg['gap'] = gap
        cfg['aspectwidth'] = aspectwidth
        cfg['aspectheight'] = aspectheight
        cfg['scale'] = scale
        cfg['alignh'] = alignh
        cfg['alignv'] = alignv
        cfg['caption'] = str(caption)
        cfg['captionh'] = captionh if caption else savedCaptionh
        cfg['removeframe'] = str(removeframe)
        cfg['alternateborder'] = str(alternateborder)
        with open(configFile, 'w') as configfile:
            config.write(configfile)

    if int(aspectheight) == 0:
        aspectratio = 0    # fill entire frame
    else:
        aspectratio = int(aspectwidth) / int(aspectheight)

    return ScPhotoBookLayoutMaker(int(cols), int(rows), float(gap), float(aspectratio),
        float(scale), alignh, alignv, float(captionh), removeframe, alternateborder)

##################################################
# Start program

def main():
    if scribus.haveDoc() == 0:
        scribus.messageBox(tr("Error: No document open"),
            tr("Please, create (or open) a document before running this script ..."),
            scribus.ICON_WARNING,scribus.BUTTON_OK)
        return
    
    try:
        scribus.statusMessage(tr('Running script...'))
        scribus.progressReset()
        unit = scribus.getUnit()
        spblm = askParameters()
        if spblm is not None:
            spblm.createLayout()
    finally:
        if scribus.haveDoc():
            scribus.redrawAll()
        scribus.setUnit(unit)
        scribus.statusMessage(tr('Done.'))
        scribus.progressReset()

if __name__ == '__main__':
    main()
