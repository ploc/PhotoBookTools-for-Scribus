# PhotoBookTools-for-Scribus

‘PhotoBook Tools’ is a collection of scripts and tricks intended to create photo album pages in a fast and flexible way with Scribus. Please read the ‘Instructions’-file for installation and use!

Summary of workflow:
1) ‘PhotoBookLayoutMaker’-script generates image frame layouts (you can save them in the Scrapbook for future use).
2) Insert images in bulk into your image frames.
3) ‘PhotoBookFillFramesCentered’-script performs automatically a maximal fill of the selected image frames. If needed you can manually adjust.
4) ‘PhotoBookImageCropResize’-script will crop your images to the image frames and resize them to the desired dpi (reduction of file size).
5) Edit caption texts (if you have created them in step 1).
6) Export your photo book to pdf or other formats.

Alternative for steps 1 to 3: the ‘PhotoBookWebGUI’-script opens a web page in your browser to build the whole book: choose the page size (when no document is open), pick the images of the book on your drive, add pages or double pages, then select images and click one of the proposed layouts for the page or double page. Frames are created in the Scribus document with the images filled and centered; captions and text blocks can then be written in Scribus. In the page you can also crop and zoom an image in its frame, drag images onto frames or between frames, insert double pages between existing ones, reorder double pages by dragging them, choose layouts with one image across the fold of a double page, and undo the last actions (until the book is saved). Click a caption or a text block to write its text; changing the options (captions, text block, spacing…) updates the current layout of the page. HEIC images are converted to JPEG (on macOS, or with Pillow installed). Keep ‘PhotoBookWebGUI.html’, ‘PhotoBookWebGUI.cfg’ and ‘PhotoBookLanguage.py’ in the same folder as the script. Scribus does not respond while the web page is open: press ‘Close’ in the page to come back to Scribus.

Emojis as stickers (PhotoBookWebGUI):
Scribus cannot print color emojis in texts (emojis typed in a caption disappear from the printed book). Use instead the ‘Sticker’ button above the page: click an emoji of the list, or type or paste any other emoji in the ‘Other emoji’ field (emoji picker: Ctrl+Cmd+Space on Mac, Windows+. on Windows), and it is placed on the page as a color image (PNG with a transparent background, 1024 pixels), that you can drag anywhere on the page or double page, resize or delete. The images are saved in a ‘PhotoBook stickers’ folder next to the book (or next to its images while the book is not saved yet): keep this folder with the book. When the computer is connected to the internet, the stickers are drawn from Twemoji (https://github.com/jdecked/twemoji), graphics licensed under CC-BY 4.0: credit them in your book, for example ‘Emojis: Twemoji, © Twitter and other contributors, CC-BY 4.0’. Without internet, the emojis of your system are used (Apple, Microsoft or Google emojis, which are less sharp when printed large, and whose use is ruled by their owners).

A little demo video: https://www.youtube.com/watch?v=3bcF4KhCCJg

For Scribus 1.5.6 and higher (needs Python 3; tested in Windows 10 and Linux).

![PhotoBookTools.jpg](https://raw.githubusercontent.com/RaffertyR/PhotoBookTools-for-Scribus/main/PhotoBookTools.jpg)
