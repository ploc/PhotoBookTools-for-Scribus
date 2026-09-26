#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
VERSION: 1.0 of 2026-09-24
AUTHOR: Rafferty River (layout patterns from PhotoBookLayoutMaker).
LICENSE: GNU GENERAL PUBLIC LICENSE Version 3, 29 June 2007.
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY.

DESCRIPTION & USAGE:
(tested on Scribus 1.5.6+ with Python 3 on Windows 10 and Linux).

PhotoBookWebGUI is a script for making photo books in Scribus.

The interface is a web page (PhotoBookWebGUI.html) opened in your
browser: create the book (or continue the open document), pick the images
of the book, add pages, and choose layouts for the images on each page
or double page. The frames are created in the Scribus document; captions
and texts can then be written in Scribus. The script serves the page on this computer only
(127.0.0.1) and stops when you press 'Close' or close the browser tab.
Scribus does not respond to clicks while the page is open.
"""
##################################################
# imports
import sys, platform, os, json, time, secrets, struct, mimetypes, webbrowser
import shutil, subprocess, tempfile, hashlib, base64
from configparser import ConfigParser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

try:
    import scribus
    from scribus import *
except ImportError:
    print("This Python script is written for the Scribus \
      scripting interface.")
    print("It can only be run from within Scribus.")
    sys.exit(1)

# translations (PhotoBookLanguage.py must be in the same folder)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PhotoBookLanguage import tr, CURRENT as TRANSLATION

python_version = platform.python_version()
if python_version[0:1] != "3":
    print("This script runs only with Python 3.")
    messageBox(tr("Script failed"),
        tr("This script runs only with Python 3."),
        ICON_CRITICAL)
    sys.exit(1)

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(HERE, 'PhotoBookWebGUI.cfg')
PATTERNS_FILE = os.path.join(HERE, 'PhotoBookMyPatterns.json')
PAGE_FILE = os.path.join(HERE, 'PhotoBookWebGUI.html')

UNSAVED_FILE = os.path.join(HERE, 'PhotoBookWebGUI.unsaved.json')
CACHE_DIR = os.path.join(tempfile.gettempdir(), 'PhotoBookWebGUI')

IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.tif', '.tiff', '.gif', '.bmp', '.webp', '.psd',
    '.heic', '.heif')
BROWSER_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp')
CONVERT_EXTENSIONS = ('.heic', '.heif')    # converted to JPEG, Scribus cannot load them
UNIT_NAMES = ['pt', 'mm', 'in', 'p', 'cm', 'c']
POINTS_PER_UNIT = [1.0, 72 / 25.4, 72.0, 12.0, 72 / 2.54, 12.7878]
ITEM_PREFIX = 'PhotoBook'    # items created by this script, replaced by a new layout
TRASH_LAYER = 'PhotoBook undo'    # hidden layer of the removed items, until saved
SIZE_ATTRIBUTE = 'PhotoBookImageSize'    # size of the image at scale 1, in points
LAYOUT_ATTRIBUTE = 'PhotoBookLayout'    # layout of the page the item was created with
ROLE_ATTRIBUTE = 'PhotoBookRole'    # image, caption or text
SLOT_ATTRIBUTE = 'PhotoBookSlot'    # order of the item in its layout
FORMAT_ATTRIBUTE = 'PhotoBookTextFormat'    # font, size, color, style of a text written by the page
SOURCE_ATTRIBUTE = 'PhotoBookSource'    # image file before rotation
ROTATION_ATTRIBUTE = 'PhotoBookRotation'    # rotation of the image, in degrees clockwise
UNDO_STEPS = 30

##################################################
# patterns (as in PhotoBookLayoutMaker): a grid of cols x rows cells, each frame covers
# [col, row, colspan, rowspan] cells of the grid

def grid(cols, rows):
    return {'cols': cols, 'rows': rows,
        'cells': [[c, r, 1, 1] for r in range(rows) for c in range(cols)]}

BUILTIN_PATTERNS = [
    grid(1, 1),
    grid(2, 1), grid(1, 2),
    {'cols': 3, 'rows': 1, 'cells': [[0, 0, 2, 1], [2, 0, 1, 1]]},
    grid(3, 1), grid(1, 3),
    {'cols': 2, 'rows': 2, 'cells': [[0, 0, 1, 2], [1, 0, 1, 1], [1, 1, 1, 1]]},
    {'cols': 2, 'rows': 2, 'cells': [[0, 0, 1, 1], [0, 1, 1, 1], [1, 0, 1, 2]]},
    {'cols': 2, 'rows': 2, 'cells': [[0, 0, 2, 1], [0, 1, 1, 1], [1, 1, 1, 1]]},
    {'cols': 2, 'rows': 2, 'cells': [[0, 0, 1, 1], [1, 0, 1, 1], [0, 1, 2, 1]]},
    grid(2, 2), grid(4, 1), grid(1, 4),
    {'cols': 3, 'rows': 3, 'cells': [[0, 0, 2, 3], [2, 0, 1, 1], [2, 1, 1, 1], [2, 2, 1, 1]]},
    {'cols': 3, 'rows': 3, 'cells': [[0, 0, 3, 2], [0, 2, 1, 1], [1, 2, 1, 1], [2, 2, 1, 1]]},
    {'cols': 3, 'rows': 2, 'cells': [[0, 0, 1, 1], [1, 0, 1, 1], [2, 0, 1, 1], [0, 1, 3, 1]]},
    {'cols': 4, 'rows': 2, 'cells': [[0, 0, 2, 2], [2, 0, 1, 1], [3, 0, 1, 1],
        [2, 1, 1, 1], [3, 1, 1, 1]]},
    {'cols': 6, 'rows': 2, 'cells': [[0, 0, 3, 1], [3, 0, 3, 1],
        [0, 1, 2, 1], [2, 1, 2, 1], [4, 1, 2, 1]]},
    grid(3, 2), grid(2, 3),
    {'cols': 3, 'rows': 3, 'cells': [[0, 0, 2, 2], [2, 0, 1, 1], [2, 1, 1, 1],
        [0, 2, 1, 1], [1, 2, 1, 1], [2, 2, 1, 1]]},
    grid(4, 2), grid(2, 4),
    grid(3, 3),
]

##################################################
# image files: size, EXIF orientation and embedded thumbnail,
# read from the file headers (no PIL needed)

def readExif(tiff, base, info):
    """ Read orientation and thumbnail position from an EXIF (TIFF) block."""
    endian = '<' if tiff[:2] == b'II' else '>'
    u16 = lambda o: struct.unpack(endian + 'H', tiff[o:o + 2])[0]
    u32 = lambda o: struct.unpack(endian + 'I', tiff[o:o + 4])[0]
    def ascii(entry):
        count = u32(entry + 4)
        offset = u32(entry + 8) if count > 4 else entry + 8
        return tiff[offset:offset + count].rstrip(b'\0').decode('ascii', 'replace')
    ifd = u32(4)
    count = u16(ifd)
    resolution, unit = None, 2
    for i in range(count):
        entry = ifd + 2 + 12 * i
        tag = u16(entry)
        if tag == 0x0132 and 'date' not in info:    # DateTime (of the file)
            info['date'] = ascii(entry)
        elif tag == 0x8769:    # Exif IFD: DateTimeOriginal, when the picture was taken
            exif = u32(entry + 8)
            for j in range(u16(exif)):
                e = exif + 2 + 12 * j
                if u16(e) == 0x9003:
                    info['date'] = ascii(e)
        elif tag == 0x0112:
            info['orientation'] = u16(entry + 8)
        elif tag == 0x011a:    # XResolution, a rational
            offset = u32(entry + 8)
            if u32(offset + 4):
                resolution = u32(offset) / u32(offset + 4)
        elif tag == 0x0128:    # ResolutionUnit: 2 inch, 3 cm
            unit = u16(entry + 8)
    if resolution:
        info['dpi'] = resolution * 2.54 if unit == 3 else resolution
    ifd = u32(ifd + 2 + 12 * count)    # IFD1 holds the thumbnail
    if ifd:
        offset = length = 0
        for i in range(u16(ifd)):
            entry = ifd + 2 + 12 * i
            if u16(entry) == 0x0201:
                offset = u32(entry + 8)
            elif u16(entry) == 0x0202:
                length = u32(entry + 8)
        if offset and length:
            info['thumbnail'] = (base + offset, length)

def readImageInfo(path):
    """ dict with 'size' (width, height as displayed), 'orientation', 'dpi',
        'date' (when the picture was taken, ISO) and 'thumbnail' (offset, length) when found."""
    info = {}
    try:
        with open(path, 'rb') as f:
            head = f.read(24)
            if head[:8] == b'\x89PNG\r\n\x1a\n':
                info['size'] = struct.unpack('>II', head[16:24])
            elif head[:2] == b'\xff\xd8':
                f.seek(2)
                while True:
                    byte = f.read(1)
                    if not byte:
                        break
                    if byte != b'\xff':
                        continue
                    marker = f.read(1)
                    while marker == b'\xff':
                        marker = f.read(1)
                    if not marker:
                        break
                    m = marker[0]
                    if m == 0x01 or 0xd0 <= m <= 0xd8:
                        continue
                    if m in (0xd9, 0xda):    # end of image, start of scan
                        break
                    length = struct.unpack('>H', f.read(2))[0]
                    start = f.tell()
                    if m == 0xe0:    # JFIF: density, 1 dpi, 2 dots per cm
                        segment = f.read(length - 2)
                        if segment[:5] == b'JFIF\0' and segment[7] in (1, 2) and 'dpi' not in info:
                            density = struct.unpack('>H', segment[8:10])[0]
                            if density:
                                info['dpi'] = density * 2.54 if segment[7] == 2 else density
                    elif m == 0xe1 and 'orientation' not in info:
                        segment = f.read(length - 2)
                        if segment[:6] == b'Exif\0\0':
                            readExif(segment[6:], start + 6, info)
                    elif 0xc0 <= m <= 0xcf and m not in (0xc4, 0xc8, 0xcc):
                        height, width = struct.unpack('>xHH', f.read(5))
                        info['size'] = (width, height)
                        break
                    f.seek(start + length - 2)
    except (OSError, struct.error, IndexError):
        pass
    date = info.get('date', '')    # 'YYYY:MM:DD HH:MM:SS' to ISO
    if len(date) >= 19 and date[:4].isdigit() and date[:4] != '0000':
        info['date'] = date[:10].replace(':', '-') + 'T' + date[11:19]
    elif 'date' in info:
        del info['date']
    if 'size' in info and info.get('orientation', 1) >= 5:    # rotated 90°
        info['size'] = (info['size'][1], info['size'][0])
    return info

##################################################
# conversion of the images the browser or Scribus cannot show (HEIC, TIFF, PSD):
# sips on macOS, or Pillow when it is installed

def findConverter():
    if sys.platform == 'darwin' and shutil.which('sips'):
        return 'sips'
    try:
        import PIL.Image
        return 'pil'
    except ImportError:
        return None

CONVERTER = findConverter()

def convertImage(path, out, size=None):
    """ Write a JPEG copy of the image, at most size pixels wide and high. True if done."""
    try:
        if CONVERTER == 'sips':
            command = ['sips', '-s', 'format', 'jpeg'] + (['-Z', str(size)] if size else []) + [path, '--out', out]
            subprocess.run(command, capture_output=True, timeout=120)
            return os.path.isfile(out)
        if CONVERTER == 'pil':
            from PIL import Image, ImageOps
            with Image.open(path) as image:
                image = ImageOps.exif_transpose(image).convert('RGB')
                if size:
                    image.thumbnail((size, size))
                image.save(out, 'JPEG', quality=90)
            return True
    except Exception:
        pass
    return False

def cachedPreview(path, size):
    """ JPEG preview of an image for the browser, kept in a temporary folder."""
    if not CONVERTER:
        return None
    key = hashlib.sha1(('%s %s %s' % (path, os.path.getmtime(path), size)).encode('utf-8')).hexdigest()
    out = os.path.join(CACHE_DIR, key + '.jpg')
    if not os.path.isfile(out):
        os.makedirs(CACHE_DIR, exist_ok=True)
        if not convertImage(path, out, size):
            return None
    return out

##################################################
# rotated images: a copy with another EXIF orientation for JPEG (no recompression,
# Scribus follows the EXIF orientation), a rotated copy made by the converter otherwise

# EXIF orientation -> matrix giving the displayed image from the stored one
ORIENTATIONS = {1: (1, 0, 0, 1), 2: (-1, 0, 0, 1), 3: (-1, 0, 0, -1), 4: (1, 0, 0, -1),
    5: (0, 1, 1, 0), 6: (0, -1, 1, 0), 7: (0, -1, -1, 0), 8: (0, 1, -1, 0)}

def rotateOrientation(orientation, degrees):
    """ EXIF orientation of the image turned by 'degrees' clockwise (a multiple of 90)."""
    a, b, c, d = ORIENTATIONS.get(orientation, ORIENTATIONS[1])
    for i in range(degrees // 90 % 4):    # clockwise quarter turn: (0, -1, 1, 0) x matrix
        a, b, c, d = -c, -d, a, b
    return next(o for o, m in ORIENTATIONS.items() if m == (a, b, c, d))

def withOrientation(data, orientation):
    """ JPEG bytes with this EXIF orientation: the tag is changed where it is, or a small
        EXIF block with it is put first."""
    pos = 2
    while pos + 4 <= len(data) and data[pos] == 0xff:
        marker, length = data[pos + 1], struct.unpack('>H', data[pos + 2:pos + 4])[0]
        if marker == 0xda:
            break
        if marker == 0xe1 and data[pos + 4:pos + 10] == b'Exif\0\0':
            base = pos + 10
            endian = '<' if data[base:base + 2] == b'II' else '>'
            ifd = base + struct.unpack(endian + 'I', data[base + 4:base + 8])[0]
            for i in range(struct.unpack(endian + 'H', data[ifd:ifd + 2])[0]):
                entry = ifd + 2 + 12 * i
                if struct.unpack(endian + 'H', data[entry:entry + 2])[0] == 0x0112:
                    return data[:entry + 8] + struct.pack(endian + 'H', orientation) + data[entry + 10:]
            break
        pos += 2 + length
    tiff = b'II*\0' + struct.pack('<I', 8) + struct.pack('<H', 1) \
        + struct.pack('<HHIHH', 0x0112, 3, 1, orientation, 0) + struct.pack('<I', 0)
    app1 = b'Exif\0\0' + tiff
    return data[:2] + b'\xff\xe1' + struct.pack('>H', len(app1) + 2) + app1 + data[2:]

def rotatedCopy(source, degrees):
    """ The image turned by 'degrees' clockwise, in a 'PhotoBook rotated' folder next to it."""
    degrees %= 360
    if not degrees:
        return source
    folder = os.path.join(os.path.dirname(source), 'PhotoBook rotated')
    stem, ext = os.path.splitext(os.path.basename(source))
    jpeg = ext.lower() in ('.jpg', '.jpeg')
    out = os.path.join(folder, '%s-%d%s' % (stem, degrees, ext if jpeg else '.png'))
    if os.path.isfile(out) and os.path.getmtime(out) >= os.path.getmtime(source):
        return out
    os.makedirs(folder, exist_ok=True)
    if jpeg:
        with open(source, 'rb') as f:
            data = f.read()
        orientation = readImageInfo(source).get('orientation', 1)
        with open(out, 'wb') as f:
            f.write(withOrientation(data, rotateOrientation(orientation, degrees)))
        return out
    if CONVERTER == 'sips':
        subprocess.run(['sips', '-s', 'format', 'png', '-r', str(degrees), source, '--out', out],
            capture_output=True, timeout=120)
    elif CONVERTER == 'pil':
        from PIL import Image, ImageOps
        with Image.open(source) as image:
            ImageOps.exif_transpose(image).rotate(-degrees, expand=True).save(out)
    if not os.path.isfile(out):
        raise ValueError(tr('This image cannot be rotated: no converter (sips or Pillow) found.'))
    return out

##################################################
class ScPhotoBookWebGUI:
    """ PhotoBookWebGUI itself: the actions of the web page on the document.
        Items removed by an action go to a hidden layer so that it can be undone;
        this layer is emptied when the document is saved and when the page is closed."""

    def __init__(self):
        """ Setup basic things """
        self.config = ConfigParser()
        self.config.read(CONFIG_FILE)
        self.pool = self.readPool()    # images chosen for the book
        self.undoSteps = []            # [{'label', 'undo': [functions], 'trash': [items]}]
        self.step = None
        self.sizes = {}                # image file -> size in points, estimated from the file
        self.pixels = {}               # image file -> size in pixels
        self.styled = {}               # text frame -> (text, formatted in Scribus)
        self.changed = False           # changes not saved

    # --- undo

    def action(self, label, function, *args):
        """ Run an action of the page, recording how to undo it."""
        self.step = {'label': label, 'undo': [], 'trash': []}
        try:
            result = function(*args)
        finally:
            if self.step['undo']:
                self.undoSteps.append(self.step)
                while len(self.undoSteps) > UNDO_STEPS:
                    self.purge(self.undoSteps.pop(0)['trash'])
            self.step = None
            self.changed = True
            docChanged(1)
            redrawAll()
        if result.get('document'):    # computed before this step was recorded
            result['document']['undo'] = tr(self.undoSteps[-1]['label']) if self.undoSteps else None
        return result

    def undo(self):
        if self.undoSteps:
            for function in reversed(self.undoSteps.pop()['undo']):
                function()
            deselectAll()
            docChanged(1)
            redrawAll()
        return {'document': self.document()}

    def trashLayer(self):
        if TRASH_LAYER not in getLayers():
            active = getActiveLayer()
            createLayer(TRASH_LAYER)    # becomes the active layer
            setLayerVisible(TRASH_LAYER, False)
            setLayerPrintable(TRASH_LAYER, False)
            setActiveLayer(active)

    def layerOf(self, name, page):
        for layer in getLayers():
            if name in getAllObjects(page=page - 1, layer=layer):
                return layer
        return getActiveLayer()

    def trash(self, name, page):
        """ Remove an item, it can come back with undo."""
        layer = self.layerOf(name, page)
        self.trashLayer()
        sendToLayer(TRASH_LAYER, name)
        self.step['trash'].append(name)
        self.step['undo'].append(lambda: sendToLayer(layer, name))

    def itemPage(self, name):
        """ Page of an item (getItemPageNumber is missing in Scribus 1.5)."""
        if hasattr(scribus, 'getItemPageNumber'):
            return scribus.getItemPageNumber(name) + 1
        for page in range(1, pageCount() + 1):
            if name in getAllObjects(page=page - 1):
                return page
        return currentPage()

    def snapshot(self, frame):
        """ Keep a copy of the frame in the trash, to undo its changes."""
        page = self.itemPage(frame)
        layer = self.layerOf(frame, page)
        copy = duplicateObjects([frame])[0]
        deselectAll()
        self.trashLayer()
        sendToLayer(TRASH_LAYER, copy)
        self.step['trash'].append(copy)
        def restore():
            if objectExists(frame):
                deleteObject(frame)
            sendToLayer(layer, copy)
            setItemName(frame, copy)
        self.step['undo'].append(restore)

    def purge(self, names):
        for name in names:
            if objectExists(name):
                deleteObject(name)

    def emptyTrash(self):
        """ Delete the removed items: the document is saved or the page closed."""
        self.undoSteps = []
        if haveDoc() and TRASH_LAYER in getLayers():
            for page in range(1, pageCount() + 1):
                self.purge(getAllObjects(page=page - 1, layer=TRASH_LAYER))
            deleteLayer(TRASH_LAYER)

    def trashed(self, page):
        if TRASH_LAYER not in getLayers():
            return set()
        return set(getAllObjects(page=page - 1, layer=TRASH_LAYER))

    # --- document

    def document(self):
        if not haveDoc():
            return None
        pages = self.pages()
        # Scribus says 'left page' for all the pages of a single sided document:
        # they are shown as single pages (side 1), not as incomplete double pages
        facing = any(p['side'] != 0 for p in pages)
        if not facing:
            for p in pages:
                p['side'] = 1
        return {'name': getDocName(), 'unit': UNIT_NAMES[getUnit()], 'pages': pages, 'facing': facing,
            'undo': tr(self.undoSteps[-1]['label']) if self.undoSteps else None}

    def role(self, name):
        for attribute in getObjectAttributes(name):
            if attribute.get('Name') == ROLE_ATTRIBUTE:
                return attribute.get('Value')
        return None

    def pageItems(self, page):
        """ Items of a page, without the removed ones."""
        trashed = self.trashed(page)
        return [name for name in getAllObjects(page=page - 1) if name not in trashed]

    def pages(self):
        """ Pages with their size, side (0 left, 1 middle, 2 right) and items.
            Coordinates are relative to each page, in document units."""
        result = []
        current = currentPage()
        for page in range(1, pageCount() + 1):
            gotoPage(page)
            width, height = getPageNSize(page)
            top, left, right, bottom = getPageNMargins(page)
            items = []
            for name in self.pageItems(page):
                objectType = getObjectType(name)
                x, y = getPosition(name)
                w, h = getSize(name)
                item = {'name': name, 'x': x, 'y': y, 'w': w, 'h': h,
                    'kind': {'ImageFrame': 'image', 'TextFrame': 'text'}.get(objectType, 'other'),
                    'app': name.startswith(ITEM_PREFIX)}
                attributes = {a.get('Name'): a.get('Value') for a in getObjectAttributes(name)}
                item['layout'] = attributes.get(LAYOUT_ATTRIBUTE)
                item['role'] = attributes.get(ROLE_ATTRIBUTE) or item['kind']
                item['slot'] = int(attributes.get(SLOT_ATTRIBUTE) or 0)
                if objectType == 'ImageFrame':
                    item['image'] = getImageFile(name)
                    if item['image']:
                        item['crop'] = self.imageRect(name)
                        item['flip'] = [bool(getProperty(name, 'imageFlippedH')),
                            bool(getProperty(name, 'imageFlippedV'))]
                        item['source'] = attributes.get(SOURCE_ATTRIBUTE) or item['image']
                        item['rotation'] = int(attributes.get(ROTATION_ATTRIBUTE) or 0)
                        if item['image'] not in self.pixels:
                            self.pixels[item['image']] = readImageInfo(item['image']).get('size')
                        item['pixels'] = self.pixels[item['image']]
                elif objectType == 'TextFrame':
                    selectText(0, 0, name)    # getAllText gives only the selected text, if any
                    item['text'] = getAllText(name).replace('\r', '\n')
                    item['fontsize'] = getFontSize(name) / POINTS_PER_UNIT[getUnit()]
                    item['styled'] = self.isStyled(name, item['text'], attributes.get(FORMAT_ATTRIBUTE))
                items.append(item)
            try:
                side = getPageType(page)
            except TypeError:    # older Scribus: type of the current page
                side = getPageType()
            result.append({'page': page, 'side': side, 'width': width, 'height': height,
                'margins': {'top': top, 'left': left, 'right': right, 'bottom': bottom},
                'items': items})
        gotoPage(current)
        return result

    def newDocument(self, width, height, margin, bleed):
        """ New photo book in millimeters: facing pages, the first one alone on the right."""
        if haveDoc():    # already created, e.g. by a click after an error
            return {'document': self.document()}
        newDocument((width, height), (margin, margin, margin, margin), PORTRAIT, 1,
            UNIT_MILLIMETERS, PAGE_2, 1, 1)
        setBleeds(bleed, bleed, bleed, bleed)
        self.pool = []    # not the images of a previous unsaved book of the same name
        self.writePool()
        return {'document': self.document(), 'pool': self.poolInfo()}

    def addPages(self, count):
        for i in range(count):
            newPage(-1)
            self.step['undo'].append(lambda: deletePage(pageCount()))
        return {'document': self.document()}

    def insertPages(self, after, count):
        """ Insert pages after the page 'after' (2 pages keep the double pages together)."""
        for i in range(count):
            if after == pageCount():
                newPage(-1)
            else:
                newPage(after + 1)
            self.step['undo'].append(lambda: deletePage(after + 1))
        return {'document': self.document()}

    def movePages(self, mapping):
        """ Move the content of pages: mapping {page: new page}. The pages themselves
            stay in place, so left and right pages keep their side."""
        moves = []
        for source, target in mapping.items():
            if source == target:
                continue
            gotoPage(source)
            for name in getAllObjects(page=source - 1):    # removed items too, for undo
                x, y = getPosition(name)
                moves.append((name, target, x, y))
        errors = []
        for name, target, x, y in moves:
            gotoPage(target)
            try:
                moveObjectAbs(x, y, name)
            except Exception as e:
                errors.append(name + ': ' + str(e))
        inverse = {target: source for source, target in mapping.items()}
        if self.step:    # not when undoing
            self.step['undo'].append(lambda: self.movePages(inverse))
        return {'document': self.document(), 'errors': errors}

    def reorder(self, order):
        """ order: first pages of the double pages in their new order."""
        slots = sorted(order)
        mapping = {}
        for slot, left in zip(slots, order):
            mapping[left] = slot
            mapping[left + 1] = slot + 1
        return self.movePages(mapping)

    def clearPages(self, pages):
        for page in pages:
            for name in self.pageItems(page):
                self.trash(name, page)
        return {'document': self.document()}

    def save(self, path):
        """ Save the book. The removed items stay in the hidden, non printable undo layer
            until the page is closed, so that undo still works."""
        if path:
            saveDocAs(path)
        else:
            saveDoc()
        self.writePool()
        self.changed = False
        return {'document': self.document(), 'saved': time.strftime('%H:%M:%S')}

    def finish(self, save):
        """ The page is closed: empty the undo layer, and save the book if it has a file."""
        if not haveDoc():
            return {'saved': False}
        trash = TRASH_LAYER in getLayers()
        self.emptyTrash()
        saved = False
        if save and os.path.isabs(getDocName()) and (self.changed or trash):
            saveDoc()
            self.writePool()
            saved = True
        self.changed = False
        return {'saved': saved}

    # --- layout

    def ensureStyles(self):
        defineColorCMYK("frameFillColor", 0, 0, 0, 64) # default is Light Grey
        # create 2 frame border styles (line width is measured in points)
        defineColorCMYK("frameBorderColor1", 0, 0, 0, 200) # default is Dark Grey
        createCustomLineStyle("frameBorderLineStyle1",
            [{'Color': "frameBorderColor1", 'Width': 1}])
        defineColorCMYK("frameBorderColor2", 0, 0, 0, 0) # default is White
        createCustomLineStyle("frameBorderLineStyle2",
            [{'Color': "frameBorderColor2", 'Width': 1}])

    def textStyle(self, name, height, lines):
        """ Paragraph style whose font fits 'lines' lines in 'height' document units."""
        points = height * POINTS_PER_UNIT[getUnit()]
        fontsize = max(6, min(14, round(points / lines / 1.4)))
        createCharStyle(name=name + "Char", fontsize=fontsize)
        createParagraphStyle(name=name, linespacingmode=0,
            alignment=ALIGN_CENTERED if lines == 1 else ALIGN_LEFT, charstyle=name + "Char")
        return name

    def imageSize(self, frame):
        """ Size of the image in points at scale 1: measured when the image was placed,
            or estimated from the file."""
        for attribute in getObjectAttributes(frame):
            if attribute.get('Name') == SIZE_ATTRIBUTE:
                w, h = attribute['Value'].split(',')
                return float(w), float(h)
        path = getImageFile(frame)
        if path not in self.sizes:
            info = readImageInfo(path)
            dpi = info.get('dpi') or 72
            size = info.get('size')
            self.sizes[path] = (size[0] * 72 / dpi, size[1] * 72 / dpi) if size else None
        return self.sizes[path]

    def imageRect(self, frame):
        """ Where the image is drawn, relative to the frame, in document units."""
        size = self.imageSize(frame)
        if not size:
            return None
        sx, sy = getImageScale(frame)
        ox, oy = getImageOffset(frame)    # always in points
        f = POINTS_PER_UNIT[getUnit()]
        return [ox / f, oy / f, size[0] * sx / f, size[1] * sy / f]

    def placeImage(self, frame, image, zoom=1.0, cx=0.5, cy=0.5):
        """ Load the image, measure it, then fill the frame (centered on cx, cy)."""
        loadImage(image, frame)
        unit = getUnit()
        setUnit(0)    # issue with units other than points
        try:
            setScaleImageToFrame(True, False, frame)
            setScaleImageToFrame(False, False, frame)
            sx, sy = getImageScale(frame)
            w, h = getSize(frame)
        finally:
            setUnit(unit)
        self.setAttribute(frame, SIZE_ATTRIBUTE, '%f,%f' % (w / sx, h / sy))
        self.setCrop(frame, zoom, cx, cy)

    def setAttribute(self, frame, name, value):
        attributes = [a for a in getObjectAttributes(frame) if a.get('Name') != name]
        attributes.append({'Name': name, 'Type': 'string', 'Value': value,
            'Parameter': '', 'Relationship': 'none', 'RelationshipTo': '', 'AutoAddTo': 'none'})
        setObjectAttributes(attributes, frame)

    def charFormats(self, frame):
        """ The different (font, size, color, paragraph style) of the characters."""
        formats = set()
        for i in range(min(getTextLength(frame), 5000)):
            selectText(i, 1, frame)
            formats.add((getFont(frame), round(getFontSize(frame), 2), getTextColor(frame), getParagraphStyle(frame)))
        selectText(0, 0, frame)    # else getAllText gives only the selected text
        deselectAll()
        return formats

    def isStyled(self, frame, text, reference):
        """ True if the text was formatted in Scribus: not all in the format given by the page
            (the same font, size, color and paragraph style everywhere)."""
        cached = self.styled.get(frame)
        if cached and cached[0] == text:
            return cached[1]
        formats = self.charFormats(frame) if text else set()
        styled = len(formats) > 1
        if not styled and formats and reference:
            styled = list(formats.pop()) != json.loads(reference)
        self.styled[frame] = (text, styled)
        return styled

    def writeText(self, frame, text):
        """ Replace the text: all of it in the paragraph style of the frame
            (PhotoBookText or PhotoBookCaption for the frames of the page)."""
        style = getParagraphStyle(frame)
        setText(text, frame)
        if style:
            setParagraphStyle(style, frame)
        if text:    # the format given by the page, to know later if it was changed in Scribus
            formats = self.charFormats(frame)
            if len(formats) == 1:
                self.setAttribute(frame, FORMAT_ATTRIBUTE, json.dumps(list(formats.pop())))
        self.styled[frame] = (text.replace('\r', '\n'), False)

    def setCrop(self, frame, zoom, cx, cy):
        """ Scale the image to fill the frame, zoomed, with the point (cx, cy) of the
            image (fractions of its size) at the center of the frame if possible."""
        size = self.imageSize(frame)
        if not size:
            return
        unit = getUnit()
        setUnit(0)
        try:
            setScaleImageToFrame(False, False, frame)
            w, h = getSize(frame)
            scale = max(w / size[0], h / size[1]) * max(1.0, zoom)
            iw, ih = size[0] * scale, size[1] * scale
            ox = min(0.0, max(w - iw, w / 2 - cx * iw))
            oy = min(0.0, max(h - ih, h / 2 - cy * ih))
            setImageScale(scale, scale, frame)
            setImageOffset(ox, oy, frame)
        finally:
            setUnit(unit)

    def apply(self, pages, frames, border, layout=None):
        """ Replace the layout of the pages by the frames computed by the web page.
            frames: list of {page, kind: image, caption or text, x, y, w, h,
            image, crop: {zoom, cx, cy}, text}; layout: name of the layout, kept with the items.
            Items not created by this script must be cleared first."""
        for page in pages:
            if any(not name.startswith(ITEM_PREFIX) for name in self.pageItems(page)):
                raise ValueError(tr('Page {} is not empty: clear it first.').format(page))
        for page in pages:
            for name in self.pageItems(page):
                if self.role(name) != 'sticker':    # stickers stay on the page
                    self.trash(name, page)

        self.ensureStyles()
        errors = []
        created = []
        self.step['undo'].append(lambda: self.purge(created))
        for frame in frames:
            gotoPage(frame['page'])
            name = ITEM_PREFIX + secrets.token_hex(4)
            x, y, w, h = frame['x'], frame['y'], frame['w'], frame['h']
            if frame['kind'] == 'image':
                newFrame = createImage(x, y, w, h, name)
                created.append(newFrame)
                setFillColor("frameFillColor", newFrame)
                if border == 'white':
                    setCustomLineStyle("frameBorderLineStyle2", newFrame)
                elif border == 'dark':
                    setCustomLineStyle("frameBorderLineStyle1", newFrame)
                else:
                    setLineColor("None", newFrame)
                if frame.get('image'):
                    crop = frame.get('crop') or {}
                    try:
                        self.placeImage(newFrame, frame['image'],
                            crop.get('zoom', 1.0), crop.get('cx', 0.5), crop.get('cy', 0.5))
                    except Exception as e:
                        errors.append(os.path.basename(frame['image']) + ': ' + str(e))
            else:
                caption = frame['kind'] == 'caption'
                newFrame = createText(x, y, w, h, name)
                created.append(newFrame)
                style = self.textStyle("PhotoBookCaption" if caption else "PhotoBookText",
                    h, 1 if caption else 12)
                setText('x', newFrame)
                setParagraphStyle(style, newFrame)
                self.writeText(newFrame, frame.get('text') or (tr('Caption') if caption else tr('Your text here')))
                if caption:
                    setTextVerticalAlignment(ALIGNV_CENTERED, newFrame)
            self.setAttribute(newFrame, ROLE_ATTRIBUTE, frame['kind'])
            self.setAttribute(newFrame, SLOT_ATTRIBUTE, str(len(created)))
            if layout:
                self.setAttribute(newFrame, LAYOUT_ATTRIBUTE, layout)
        # the stickers stay above the new frames
        for page in pages:
            for name in self.pageItems(page):
                if self.role(name) == 'sticker':
                    deselectAll()
                    selectObject(name)
                    moveSelectionToFront()
        deselectAll()
        return {'document': self.document(), 'errors': errors}

    def setImage(self, frame, image):
        """ Put another image in an image frame."""
        self.snapshot(frame)
        self.placeImage(frame, image)
        return {'document': self.document()}

    def swap(self, first, second):
        """ Exchange the images of two frames (or copy one into an empty frame)."""
        images = getImageFile(first), getImageFile(second)
        for frame, image in ((second, images[0]), (first, images[1])):
            if image:
                self.snapshot(frame)
                self.placeImage(frame, image)
        return {'document': self.document()}

    def crop(self, frame, zoom, cx, cy):
        self.snapshot(frame)
        self.setCrop(frame, zoom, cx, cy)
        return {'document': self.document()}

    # --- stickers: color emojis drawn by the browser, placed as images

    def stickerFolder(self):
        name = getDocName() if haveDoc() else ''
        if os.path.isabs(name):
            base = os.path.dirname(name)
        elif self.pool:
            base = os.path.dirname(self.pool[0])
        else:
            base = os.path.expanduser('~')
        folder = os.path.join(base, 'PhotoBook stickers')
        os.makedirs(folder, exist_ok=True)
        return folder

    def addSticker(self, page, emoji, png, x, y, size):
        data = base64.b64decode(png.split(',')[-1])
        if data[:8] != b'\x89PNG\r\n\x1a\n':
            raise ValueError('not a PNG image')
        name = 'emoji-' + '-'.join('%x' % ord(c) for c in emoji if ord(c) not in (0xfe0f, 0x200d)) + '.png'
        path = os.path.join(self.stickerFolder(), name)
        if not os.path.isfile(path):
            with open(path, 'wb') as f:
                f.write(data)
        gotoPage(page)
        frame = createImage(x, y, size, size, ITEM_PREFIX + 'Sticker' + secrets.token_hex(4))
        self.step['undo'].append(lambda: self.purge([frame]))
        setFillColor('None', frame)
        setLineColor('None', frame)
        loadImage(path, frame)
        setScaleImageToFrame(True, True, frame)
        self.setAttribute(frame, ROLE_ATTRIBUTE, 'sticker')
        deselectAll()
        return {'document': self.document(), 'frame': frame}

    def moveItem(self, frame, page, x, y, w, h):
        """ Move and resize an item, possibly to another page."""
        self.snapshot(frame)
        gotoPage(page)
        sizeObject(w, h, frame)
        moveObjectAbs(x, y, frame)
        if self.role(frame) == 'sticker':
            setScaleImageToFrame(True, True, frame)
        return {'document': self.document()}

    def deleteItem(self, frame):
        self.trash(frame, self.itemPage(frame))
        return {'document': self.document()}

    def rotate(self, frame, degrees):
        """ Turn the image of the frame by a quarter turn (90 or -90)."""
        attributes = {a.get('Name'): a.get('Value') for a in getObjectAttributes(frame)}
        source = attributes.get(SOURCE_ATTRIBUTE) or getImageFile(frame)
        rotation = (int(attributes.get(ROTATION_ATTRIBUTE) or 0) + degrees) % 360
        self.snapshot(frame)
        self.placeImage(frame, rotatedCopy(source, rotation))
        self.setAttribute(frame, SOURCE_ATTRIBUTE, source)
        self.setAttribute(frame, ROTATION_ATTRIBUTE, str(rotation))
        return {'document': self.document()}

    def mirror(self, frame, horizontal):
        prop = 'imageFlippedH' if horizontal else 'imageFlippedV'
        self.snapshot(frame)
        setProperty(frame, prop, not getProperty(frame, prop))
        return {'document': self.document()}

    def editText(self, frame, text):
        self.snapshot(frame)
        self.writeText(frame, text)
        return {'document': self.document(), 'overflow': bool(textOverflows(frame))}

    # --- settings and patterns

    def saveParams(self, params):
        for key, value in params.items():
            self.config.set('DEFAULT', key, str(value))
        with open(CONFIG_FILE, 'w') as configfile:
            self.config.write(configfile)
        return {}

    def myPatterns(self):
        try:
            with open(PATTERNS_FILE) as f:
                return json.load(f)
        except (OSError, ValueError):
            return []

    def saveMyPatterns(self, patterns):
        with open(PATTERNS_FILE, 'w') as f:
            json.dump(patterns, f, indent=1)
        return {'myPatterns': patterns}

    # --- images of the book, kept next to the document in <document>.photobook.json,
    # or in PhotoBookWebGUI.unsaved.json while the document has no file

    def poolFile(self):
        name = getDocName() if haveDoc() else ''
        return os.path.splitext(name)[0] + '.photobook.json' if os.path.isabs(name) else None

    def unsavedPools(self):
        try:
            with open(UNSAVED_FILE) as f:
                return json.load(f)
        except (OSError, ValueError):
            return {}

    def readPool(self):
        if self.poolFile():
            try:
                with open(self.poolFile()) as f:
                    return json.load(f).get('images', [])
            except (OSError, ValueError):
                return []
        return self.unsavedPools().get(getDocName() if haveDoc() else '', [])

    def writePool(self):
        pools = self.unsavedPools()
        key = getDocName() if haveDoc() else ''
        if self.poolFile():
            with open(self.poolFile(), 'w') as f:
                json.dump({'images': self.pool}, f, indent=1)
            if key in pools:
                del pools[key]
            else:
                return
        else:
            pools[key] = self.pool
        with open(UNSAVED_FILE, 'w') as f:
            json.dump(pools, f, indent=1)

    def setPool(self, images):
        """ Images of the book; HEIC images are converted to JPEG for Scribus,
            in a 'PhotoBook JPEG' folder next to them."""
        pool, converted, failed = [], 0, []
        for path in images:
            if path.lower().endswith(CONVERT_EXTENSIONS):
                folder = os.path.join(os.path.dirname(path), 'PhotoBook JPEG')
                out = os.path.join(folder, os.path.splitext(os.path.basename(path))[0] + '.jpg')
                if not os.path.isfile(out):
                    os.makedirs(folder, exist_ok=True)
                    if not convertImage(path, out):
                        failed.append(os.path.basename(path))
                        continue
                    converted += 1
                path = out
            if path not in pool:
                pool.append(path)
        self.pool = pool
        self.writePool()
        return {'pool': self.poolInfo(), 'converted': converted, 'failed': failed}

    def imageInfo(self, path):
        info = readImageInfo(path)
        lower = path.lower()
        date, dateFrom = info.get('date'), 'exif'
        if not date and os.path.isfile(path):    # no EXIF date: the date of the file
            date = time.strftime('%Y-%m-%dT%H:%M:%S', time.localtime(os.path.getmtime(path)))
            dateFrom = 'file'
        return {'name': os.path.basename(path), 'path': path, 'size': info.get('size'),
            'date': date, 'dateFrom': dateFrom,
            'orientation': info.get('orientation', 1), 'thumb': 'thumbnail' in info,
            'preview': lower.endswith(BROWSER_EXTENSIONS) or bool(CONVERTER),
            'exists': os.path.isfile(path)}

    def poolInfo(self):
        return [self.imageInfo(path) for path in self.pool]

    def state(self):
        params = dict(self.config['DEFAULT'])
        folder = params.get('imagefolder', '')
        if not os.path.isdir(folder) and self.pool:
            folder = os.path.dirname(self.pool[-1])
        if not os.path.isdir(folder) and haveDoc() and os.path.isabs(getDocName()):
            folder = os.path.dirname(getDocName())
        if not os.path.isdir(folder):
            folder = os.path.expanduser('~')
        return {
            'strings': TRANSLATION,
            'params': params,
            'patterns': BUILTIN_PATTERNS,
            'myPatterns': self.myPatterns(),
            'document': self.document(),
            'pool': self.poolInfo(),
            'folder': folder,
            'converter': bool(CONVERTER),
            'language': 'fr' if TRANSLATION else 'en',
        }

    # --- image files

    def browse(self, folder):
        folder = os.path.abspath(os.path.expanduser(folder or '~'))
        dirs, images = [], []
        for name in sorted(os.listdir(folder), key=str.lower):
            if name.startswith('.'):
                continue
            path = os.path.join(folder, name)
            if os.path.isdir(path):
                dirs.append({'name': name, 'path': path})
            elif name.lower().endswith(IMAGE_EXTENSIONS):
                images.append(self.imageInfo(path))
        parent = os.path.dirname(folder)
        return {'folder': folder, 'parent': parent if parent != folder else None,
            'dirs': dirs, 'images': images}

    def thumbnail(self, path, mode):
        """ (content type, bytes) to show the image in the browser.
            mode 'thumb': the EXIF thumbnail if any, not rotated (the page rotates it),
            'auto': the EXIF thumbnail if it needs no rotation, 'full': the image."""
        if not os.path.isfile(path) or not path.lower().endswith(IMAGE_EXTENSIONS):
            return None
        if not path.lower().endswith(BROWSER_EXTENSIONS):
            path = cachedPreview(path, 1600 if mode == 'full' else 400)
            if not path:
                return None
        elif mode != 'full':
            info = readImageInfo(path)
            if 'thumbnail' in info and (mode == 'thumb' or info.get('orientation', 1) == 1):
                offset, length = info['thumbnail']
                with open(path, 'rb') as f:
                    f.seek(offset)
                    data = f.read(length)
                if data[:2] == b'\xff\xd8':
                    return 'image/jpeg', data
        with open(path, 'rb') as f:
            return mimetypes.guess_type(path)[0] or 'application/octet-stream', f.read()

##################################################
# web server: requests are handled one at a time in Scribus's main
# thread, so the handlers can call the Scribus API

class Server(HTTPServer):
    request_queue_size = 64    # the page loads many thumbnails at once

class WebApp:
    """ Serve the page and route its requests to ScPhotoBookWebGUI."""

    def __init__(self, maker):
        self.maker = maker
        self.token = secrets.token_urlsafe(16)
        self.finished = False
        self.lastRequest = time.time()
        self.closedAt = None
        app = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                app.handle(self, 'GET')

            def do_POST(self):
                app.handle(self, 'POST')

        self.server = Server(('127.0.0.1', 0), Handler)
        self.server.timeout = 0.5
        self.url = 'http://127.0.0.1:{}/?token={}'.format(self.server.server_port, self.token)

    def send(self, request, status, contentType, data):
        request.send_response(status)
        request.send_header('Content-Type', contentType)
        request.send_header('Content-Length', str(len(data)))
        request.send_header('Cache-Control', 'no-store')
        request.end_headers()
        request.wfile.write(data)

    def handle(self, request, method):
        self.lastRequest = time.time()
        url = urlparse(request.path)
        query = {k: v[0] for k, v in parse_qs(url.query).items()}
        if query.get('token') != self.token:
            return self.send(request, 403, 'text/plain', b'Forbidden')
        body = {}
        if method == 'POST':
            length = int(request.headers.get('Content-Length', 0))
            if length:
                body = json.loads(request.rfile.read(length).decode('utf-8'))
        try:
            if url.path == '/':
                with open(PAGE_FILE, 'rb') as f:
                    return self.send(request, 200, 'text/html; charset=utf-8', f.read())
            if url.path == '/image':
                result = self.maker.thumbnail(query.get('path', ''), query.get('mode', 'full'))
                if result is None:
                    return self.send(request, 404, 'text/plain', b'Not found')
                return self.send(request, 200, *result)
            result = self.route(url.path, body)
            if result is None:
                return self.send(request, 404, 'text/plain', b'Not found')
            data = json.dumps(result).encode('utf-8')
            return self.send(request, 200, 'application/json', data)
        except Exception as e:
            data = json.dumps({'error': str(e)}).encode('utf-8')
            return self.send(request, 500, 'application/json', data)

    def route(self, path, body):
        maker = self.maker
        if path == '/api/state':
            self.closedAt = None
            return maker.state()
        if path == '/api/ping':
            self.closedAt = None
            return {}
        if path == '/api/closed':    # tab closed or reloaded
            self.closedAt = time.time()
            return {}
        if path == '/api/quit':    # save and clean before Scribus is given back
            result = maker.finish(body.get('save', True))
            self.finished = True
            return result
        if path == '/api/newdocument':
            return maker.newDocument(body['width'], body['height'], body['margin'], body['bleed'])
        if path == '/api/addpages':
            return maker.action('Add pages', maker.addPages, body['count'])
        if path == '/api/insertpages':
            return maker.action('Insert pages', maker.insertPages, body['after'], body['count'])
        if path == '/api/reorder':
            return maker.action('Move a double page', maker.reorder, body['order'])
        if path == '/api/clear':
            return maker.action('Erase', maker.clearPages, body['pages'])
        if path == '/api/apply':
            return maker.action('Layout', maker.apply, body['pages'], body['frames'], body.get('border'),
                body.get('layout'))
        if path == '/api/sticker':
            return maker.action('Sticker', maker.addSticker, body['page'], body['emoji'], body['png'],
                body['x'], body['y'], body['size'])
        if path == '/api/move':
            return maker.action('Move', maker.moveItem, body['frame'], body['page'],
                body['x'], body['y'], body['w'], body['h'])
        if path == '/api/delete':
            return maker.action('Delete', maker.deleteItem, body['frame'])
        if path == '/api/rotate':
            return maker.action('Rotation', maker.rotate, body['frame'], body['degrees'])
        if path == '/api/mirror':
            return maker.action('Mirror', maker.mirror, body['frame'], body['horizontal'])
        if path == '/api/text':
            return maker.action('Text', maker.editText, body['frame'], body['text'])
        if path == '/api/setimage':
            return maker.action('Image change', maker.setImage, body['frame'], body['image'])
        if path == '/api/swap':
            return maker.action('Swap images', maker.swap, body['first'], body['second'])
        if path == '/api/crop':
            return maker.action('Crop', maker.crop, body['frame'], body['zoom'], body['cx'], body['cy'])
        if path == '/api/undo':
            return maker.undo()
        if path == '/api/save':
            return maker.save(body.get('path'))
        if path == '/api/pool':
            return maker.setPool(body['images'])
        if path == '/api/params':
            return maker.saveParams(body)
        if path == '/api/patterns':
            return maker.saveMyPatterns(body)
        if path == '/api/browse':
            return maker.browse(body.get('folder'))
        return None

    def run(self):
        """ Serve until the page is closed."""
        if not webbrowser.open(self.url):
            messageBox(tr('PhotoBook Web GUI'),
                tr('Open this address in your browser:') + '\n' + self.url, ICON_INFORMATION)
        while not self.finished:
            self.server.handle_request()
            now = time.time()
            if self.closedAt and now - self.closedAt > 5:
                self.finished = True    # closed, not reloaded
            if now - self.lastRequest > 600:
                self.finished = True    # page gone (the page pings every few seconds)
        self.server.server_close()

##################################################
# Start program

def main():
    maker = ScPhotoBookWebGUI()
    try:
        scribus.statusMessage(tr('Running script...'))
        WebApp(maker).run()
    finally:
        maker.finish(True)    # tab closed without 'Close': saved if the book has a file
        if scribus.haveDoc():
            scribus.setRedraw(True)
            scribus.redrawAll()
        scribus.statusMessage(tr('Done.'))

if __name__ == '__main__':
    main()
