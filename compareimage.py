#!/usr/bin/env python
"""Program to compare 2 images
Process these images to show the differences more clearly
and show with 3 tabs: Master image, Slave image, Diff image.
Author: Henk Speksnijder october 2013.
20130927  Version 0.73  using PYTHON-PILLOW
"""
import sys
#import os
import io
from PIL import Image, ImageChops

try:
  import gi
  gi.require_version('Gtk', '3.0')  # tell we want GTK3
except ImportError:
  print('You need to install python-gobject.')
  sys.exit(1)

try:
  #from gi.repository import Gtk, GdkPixbuf, GObject  # pylint: disable=E0611
  from gi.repository import Gtk, GdkPixbuf  # pylint: disable=E0611
except ImportError:
  print("You need to install python-Gobject or GTK3\n"
        "or set your PYTHONPATH correctly.\n"
        "try: export PYTHONPATH="
        "/usr/lib/python3.2/site-packages/")
  sys.exit(1)
# Now we have both gtk and Gtk.glade imported and run GTK v3

class tabimage(Gtk.ScrolledWindow):
  """Class on Gtk.notebook to manage 1 tabsheet with an image."""
  def __init__(self, parent):  # pylint: disable=E1002
    self.imagewidth = 0
    self.imageheight = 0
    self.ntbk = parent
    self.pixbuf = None
    self.image = None
    super().__init__()

  def imagefile(self, fn, iw, ih):
    """Load image file fn and scale to size iw * ih."""
    self.pixbuf = GdkPixbuf.Pixbuf.new_from_file(fn)
    self.image = self.imagestart(self.pixbuf, iw, ih)
    self.image.connect('draw', self.imageresize, self.pixbuf)
    self.add(self.image)
    self.imagewidth = self.pixbuf.get_width()
    self.imageheight = self.pixbuf.get_height()
    return

  def imagepixb(self, apixbuf, iw, ih):
    """apixbuf, scale to size iw * ih."""
    self.pixbuf = apixbuf
    self.image = self.imagestart(apixbuf, iw, ih)
    self.image.connect('draw', self.imageresize, self.pixbuf)
    self.add(self.image)
    self.imagewidth = apixbuf.get_width()
    self.imageheight = apixbuf.get_height()
    return

  def imagestart(self, apixbuf, targetw, targeth):
    """Make sure we start with images fit in window."""
    iw = apixbuf.get_width()
    ih = apixbuf.get_height()
    if iw > targetw or ih > targeth:
      apixbuf = self.imagezoom(apixbuf, iw, ih)
    ret = Gtk.Image.new_from_pixbuf(apixbuf)
    return ret

  def imageresize(self, imgwidget, event, apixbuf):  # pylint: disable=W0613
    """Resize image to FIT on imgwidget (an Gtk.Image)."""
    allocation = self.ntbk.get_allocation()
    aw = allocation.width  # - 40
    ah = allocation.height  # - 50
    if aw != apixbuf.get_width() or ah != apixbuf.get_height():
      zpixbuf = self.imagezoom(apixbuf, aw, ah)
      imgwidget.set_from_pixbuf(zpixbuf)
      self.imagewidth = aw  # + 40
      self.imageheight = ah  # + 50
    return

  def imagezoom(self, apixbuf, targetwidth, targetheight):
    """Return resized image from apixbuf to targetw * targeth."""
    preimg_width = apixbuf.get_width()
    preimg_height = apixbuf.get_height()
    wratio = float(preimg_width)/targetwidth
    hratio = float(preimg_height)/targetheight
    if wratio < hratio:
      zoomratio = hratio
    else:
      zoomratio = wratio
    wfinal = int(preimg_width / zoomratio)
    hfinal = int(preimg_height / zoomratio)
    zpixbuf = apixbuf.scale_simple(
        wfinal,
        hfinal,
        GdkPixbuf.InterpType.BILINEAR)
    return zpixbuf

class CompareImages(Gtk.Window):
  """Class to compare 2 images"""
  def __init__(self, fnm, fns):
    self.imgwidth = 600
    self.imgheight = 400
    self.window = Gtk.Window()
    self.window.set_title('Compare Images')
    self.window.set_size_request(self.imgwidth+40, self.imgheight+50)
    self.window.connect("destroy", Gtk.main_quit)
    #===== notebook with images =====
    self.ntbk = Gtk.Notebook()
    self.tabw1 = tabimage(self.ntbk)
    self.tabw1.imagefile(fnm, 600, 400)
    self.tabw2 = tabimage(self.ntbk)
    self.tabw2.imagefile(fns, 600, 400)
    self.pixbdif = self.imgdif(fna, fnb)
    self.tabw3 = tabimage(self.ntbk)
    self.tabw3.imagepixb(self.pixbdif, 600, 400)
    self.tabt1 = Gtk.Label("Master image")
    self.tabt2 = Gtk.Label("Slave Image")
    self.tabt3 = Gtk.Label("Differences")
    self.ntbk.append_page(self.tabw1, self.tabt1)
    self.ntbk.append_page(self.tabw2, self.tabt2)
    self.ntbk.append_page(self.tabw3, self.tabt3)
    #self.ntbk.connect("switch-page", self.ntbkswitch)
    self.window.add(self.ntbk)
    #===== Bring it On ! =====
    self.window.show_all()
    return

  def main(self):  # pylint: disable=C0111
    Gtk.main()

  def imgdif(self, fnm, fns):
    """Take 2 images and generate a image diff, Return GdkPixbuf."""
    buff1 = io.BytesIO()
    imagem = Image.open(fnm)
    images = Image.open(fns)
    imaged = ImageChops.difference(imagem, images)
    # That's all we need to compare the images.
    # Seems mold from PIL image to GTK image is weird, see:
    # http://stackoverflow.com/questions/12413645/displaying-an-image-with-pygobject-and-python-3-from-in-memory-data
    # Anyway, we need a lot of boilerplate to get there:
    imaged.save(buff1, "ppm")
    contents = buff1.getvalue()
    buff1.close()
    loader = GdkPixbuf.PixbufLoader.new_with_type('pnm')
    loader.write(contents)
    pixbuf = loader.get_pixbuf()
    loader.close()
    return pixbuf

if __name__ == "__main__":
  if sys.version[0] == 2:
    print("Error: Program designed for Python Version 3.")
    sys.exit(1)
  if len(sys.argv) < 3:
    print('You need to provide 2 filenames')
    exit(1)

  fna = sys.argv[1]
  fnb = sys.argv[2]
  app = CompareImages(fna, fnb)
  Gtk.main()
  sys.exit(0)

# 0.1 initial incomplete design by Henk Speksnijder 11 march 2013
#       Not much progress as PIL is not available for python3
# 0.5 improvements october 2013 using python-pillow
#       Meanwhile an PIL fork is developped: pillow for image processing.
#     GdkPixbuf.Scale(dest,
#         0,0              # dest_x, dest_y,
#         dest_width, dest_height,
#         0,0              #offset_x, offset_y,
#         scale_x, scale_y,
#         gtk.gdk.INTERP_BILINEAR)  # interp_type
#     The scale() method creates a transformation of the pixbuf's image by
#     scaling by scale_x and scale_y and translating by offset_x and offset_y it,
#     then rendering the rectangle (dest_x, dest_y, dest_width, dest_height) of
#     the resulting image onto the destination image specified by dest replacing
#     the previous contents.
#     Gtk3 Nieuw:   GdkPixbuf.InterpType.BILINEAR
#     Gtk2 oud was: gtk.gdk.INTERP_BILINEAR
# 0.6 GdkPixbuf.scale_simple found, is more easy.
#     Searched long and hard in the internet but cannot find how to
#     make the image scale automatic. Finally 'borrow' from mirage.
#       self.window.connect("size-allocate", self.window_resized)
#     mirage line 3148 wanted_zoomratio = self.calc_ratio(self.currimg)
#     useful, copied 3148 and line 3120 to 3132
#     VERY very interesting:
#    	  gc.collect()  # Clean up (free memory)
# 0.7 20131009 To get the image resizable try
#       with scrolled window and with  img1.connevt(....
# 0.73 20131011 change several functions to a new class tabimage
#    Wow: a lot simpler and works mutch better.
# 0.74 20131012 code cleanup (pylint)
# TO DO:
#    add information pane to compare image information
#      like filesize, date/time, w * h, extension, exif info.
#    make keys m/s/d and 1/2/3 switch tabs
#    make help-panel
#    make translations
#=============== pylintrc: ====================
# [MASTER]
# profile=no
# ignore=CVS
# persistent=no
# [MESSAGES CONTROL]
# disable=I0011
# [REPORTS]
# output-format=text
# reports=no
# [FORMAT]
# indent-string='  '
# max-line-length=100
# [DESIGN]
# max-args=7
# max-attributes=15
# [BASIC]
# class-rgx=[a-zA-Z_][a-zA-Z0-9]+$
# argument-rgx=[a-z_][a-z0-9_]{1,30}$
# variable-rgx=[a-z_][a-z0-9_]{1,30}$
# C0111 = Missing Docstring
#           some procedures are so obvious a docstring looks silly.
# E0611 = No name 'Gtk' in module 'gi.repository (line 14)
#           Due to pylint limitations it cannot scan gi-repository.
# E1002 = Use of super on old style class
#           pylint thinks ive made an old style while it IS a new stye class !
# W0613 = Unused argument 'event'
#           Yea right, the argument is build into the Gtk callback mechanism
#           and in this function i cannot invent a way to make use of it.
