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
from configparser import ConfigParser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

try:
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

IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.tif', '.tiff', '.gif', '.bmp', '.webp', '.psd')
BROWSER_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp')
UNIT_NAMES = ['pt', 'mm', 'in', 'p', 'cm', 'c']
POINTS_PER_UNIT = [1.0, 72 / 25.4, 72.0, 12.0, 72 / 2.54, 12.7878]
ITEM_PREFIX = 'PhotoBook'    # items created by this script, replaced by a new layout

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
    ifd = u32(4)
    count = u16(ifd)
    for i in range(count):
        entry = ifd + 2 + 12 * i
        if u16(entry) == 0x0112:
            info['orientation'] = u16(entry + 8)
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
    """ dict with 'size' (width, height as displayed), 'orientation'
        and 'thumbnail' (offset, length) when found."""
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
                    if m == 0xe1 and 'orientation' not in info:
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
    if 'size' in info and info.get('orientation', 1) >= 5:    # rotated 90°
        info['size'] = (info['size'][1], info['size'][0])
    return info

##################################################
class ScPhotoBookWebGUI:
    """ PhotoBookWebGUI itself: the actions of the web page on the document."""

    def __init__(self):
        """ Setup basic things """
        self.config = ConfigParser()
        self.config.read(CONFIG_FILE)
        self.pool = self.readPool()    # images chosen for the book

    # --- document

    def document(self):
        if not haveDoc():
            return None
        return {'name': getDocName(), 'unit': UNIT_NAMES[getUnit()], 'pages': self.pages()}

    def pages(self):
        """ Pages with their size, side (0 left, 1 middle, 2 right) and items.
            Coordinates are relative to each page, in document units."""
        result = []
        current = currentPage()
        for page in range(1, pageCount() + 1):
            gotoPage(page)
            width, height = getPageNSize(page)
            top, left, right, bottom = getPageNMargins(page)
            try:
                names = getAllObjects(page=page - 1)
            except TypeError:    # older Scribus: objects of the current page
                names = getAllObjects()
            items = []
            for name in names:
                objectType = getObjectType(name)
                x, y = getPosition(name)
                w, h = getSize(name)
                item = {'name': name, 'x': x, 'y': y, 'w': w, 'h': h,
                    'kind': {'ImageFrame': 'image', 'TextFrame': 'text'}.get(objectType, 'other'),
                    'app': name.startswith(ITEM_PREFIX)}
                if objectType == 'ImageFrame':
                    item['image'] = getImageFile(name)
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
        return {'document': self.document()}

    def addPages(self, count):
        for i in range(count):
            newPage(-1)
        docChanged(1)
        return {'document': self.document()}

    def clearPages(self, pages):
        for page in pages:
            gotoPage(page)
            for item in self.pageItems(page):
                deleteObject(item)
        docChanged(1)
        redrawAll()
        return {'document': self.document()}

    def pageItems(self, page):
        try:
            return getAllObjects(page=page - 1)
        except TypeError:
            gotoPage(page)
            return getAllObjects()

    def save(self, path):
        if path:
            saveDocAs(path)
        else:
            saveDoc()
        self.writePool()
        return {'document': self.document()}

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

    def fillFrameCentered(self, frame):
        """ Scale the image to fill the frame, centered (as PhotoBookFillFramesCentered)."""
        unit = getUnit()
        setUnit(0)    # issue with units other than points
        setScaleImageToFrame(True, False, frame)
        setScaleImageToFrame(False, False, frame)
        scale = getImageScale(frame)
        maxScale = max(scale)
        setImageScale(maxScale, maxScale, frame)
        width, height = getSize(frame)
        setImageOffset((width * (1 - maxScale / scale[0])) / 2,
            (height * (1 - maxScale / scale[1])) / 2, frame)
        setUnit(unit)

    def apply(self, pages, frames, border):
        """ Replace the layout of the pages by the frames computed by the web page.
            frames: list of {page, kind: image, caption or text, x, y, w, h, image}
            Items not created by this script must be cleared first."""
        for page in pages:
            if any(not name.startswith(ITEM_PREFIX) for name in self.pageItems(page)):
                raise ValueError(tr('Page {} is not empty: clear it first.').format(page))
        for page in pages:
            gotoPage(page)
            for name in self.pageItems(page):
                deleteObject(name)

        self.ensureStyles()
        errors = []
        for frame in frames:
            gotoPage(frame['page'])
            name = ITEM_PREFIX + secrets.token_hex(4)
            x, y, w, h = frame['x'], frame['y'], frame['w'], frame['h']
            if frame['kind'] == 'image':
                newFrame = createImage(x, y, w, h, name)
                setFillColor("frameFillColor", newFrame)
                if border == 'white':
                    setCustomLineStyle("frameBorderLineStyle2", newFrame)
                elif border == 'dark':
                    setCustomLineStyle("frameBorderLineStyle1", newFrame)
                else:
                    setLineColor("None", newFrame)
                if frame.get('image'):
                    try:
                        loadImage(frame['image'], newFrame)
                        self.fillFrameCentered(newFrame)
                    except Exception as e:
                        errors.append(os.path.basename(frame['image']) + ': ' + str(e))
            else:
                caption = frame['kind'] == 'caption'
                newFrame = createText(x, y, w, h, name)
                setText(tr('Caption') if caption else tr('Your text here'), newFrame)
                style = self.textStyle("PhotoBookCaption" if caption else "PhotoBookText",
                    h, 1 if caption else 12)
                setParagraphStyle(style, newFrame)
                if caption:
                    setTextVerticalAlignment(ALIGNV_CENTERED, newFrame)
        deselectAll()
        docChanged(1)
        setRedraw(True)
        redrawAll()
        return {'document': self.document(), 'errors': errors}

    def setImage(self, frame, image):
        """ Put another image in an image frame."""
        loadImage(image, frame)
        self.fillFrameCentered(frame)
        docChanged(1)
        redrawAll()
        return {'document': self.document()}

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

    # --- images of the book, kept next to the document in <document>.photobook.json

    def poolFile(self):
        name = getDocName() if haveDoc() else ''
        return os.path.splitext(name)[0] + '.photobook.json' if os.path.isabs(name) else None

    def readPool(self):
        try:
            with open(self.poolFile()) as f:
                return json.load(f).get('images', [])
        except (TypeError, OSError, ValueError):
            return []

    def writePool(self):
        if self.poolFile():
            with open(self.poolFile(), 'w') as f:
                json.dump({'images': self.pool}, f, indent=1)

    def setPool(self, images):
        self.pool = images
        self.writePool()
        return {'pool': self.poolInfo()}

    def imageInfo(self, path):
        info = readImageInfo(path)
        return {'name': os.path.basename(path), 'path': path, 'size': info.get('size'),
            'orientation': info.get('orientation', 1), 'thumb': 'thumbnail' in info,
            'preview': path.lower().endswith(BROWSER_EXTENSIONS), 'exists': os.path.isfile(path)}

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
        if not path.lower().endswith(BROWSER_EXTENSIONS) or not os.path.isfile(path):
            return None
        if mode != 'full':
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
        if path == '/api/quit':
            self.finished = True
            return {}
        if path == '/api/newdocument':
            return maker.newDocument(body['width'], body['height'], body['margin'], body['bleed'])
        if path == '/api/addpages':
            return maker.addPages(body['count'])
        if path == '/api/clear':
            return maker.clearPages(body['pages'])
        if path == '/api/apply':
            return maker.apply(body['pages'], body['frames'], body.get('border'))
        if path == '/api/setimage':
            return maker.setImage(body['frame'], body['image'])
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
    try:
        scribus.statusMessage(tr('Running script...'))
        WebApp(ScPhotoBookWebGUI()).run()
    finally:
        if scribus.haveDoc():
            scribus.setRedraw(True)
            scribus.redrawAll()
        scribus.statusMessage(tr('Done.'))

if __name__ == '__main__':
    main()
