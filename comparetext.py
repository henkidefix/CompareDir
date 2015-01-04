#!/usr/bin/python

import sys
import os
import difflib

try:
    import gi
    gi.require_version('Gtk', '3.0')  #tell we want GTK3
except:
    print('You need to install python-gobject')
    sys.exit(1)
try:
    from gi.repository import Gtk, Gdk, GdkPixbuf, GObject
except:
    print(_("You need to install python-Gobject or GTK3\n"
          "or set your PYTHONPATH correctly.\n"
          "try: export PYTHONPATH="
          "/usr/lib/python3.2/site-packages/"))
    sys.exit(1)
# Now we have both gtk and Gtk.glade imported and run GTK v3

class CompareText:
  def __init__( self, title, fsa, fsb):
    self.window = Gtk.Window()
    self.title = title
    self.window.set_title( title)
    self.window.set_size_request( 600, 400)
    self.window.connect( "destroy", Gtk.main_quit)
    self.create_interior()
    self.window.show_all()
  def create_interior( self):
    self.button1= Gtk.Button(label="Click Here")
    self.button1.connect("clicked", self.on_button_clicked)
    self.button2= Gtk.Button(label="Click There")
    self.button2.connect("clicked", self.on_button_clicked)
    self.butbox=Gtk.Box()
    self.butbox.add(self.button1)
    self.butbox.add(self.button2)

    self.textviewl = Gtk.TextView()
    self.textbufl = self.textviewl.get_buffer()
    self.scroll=Gtk.ScrolledWindow()
    self.scroll.add(self.textviewl)
    self.scroll.set_hexpand(True)
    self.scroll.set_vexpand(True)
    self.textviewr = Gtk.TextView()
    self.textbufr = self.textviewr.get_buffer()
    self.scrolr=Gtk.ScrolledWindow()
    self.scrolr.add(self.textviewr)
    self.scrolr.set_hexpand(True)
    self.scrolr.set_vexpand(True)

    self.textbox=Gtk.Box(spacing=6)
    self.textbox.add(self.scroll)
    self.textbox.add(self.scrolr)

    #self.mainbox = Gtk.VBox()
    self.mainbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
    self.mainbox.add(self.butbox)
    self.mainbox.add(self.textbox)
    #==== fill ===========
    #htag=self.textbufl.create_tag('h',size_points=16)
    self.rtag = self.textbufr.create_tag( "color", foreground="#EE1BEC") 
    self.ltag = self.textbufl.create_tag( "color", foreground="#F60A0F")
    self.showdiff(fsa,fsb)
    """
    position=self.textbufl.get_end_iter()
    self.textbufl.insert_with_tags(position,"Heading\n",htag)
    position=self.textbufl.get_end_iter()
    self.textbufl.insert(position, "some normal text\n on 2 lines\n")
    position=self.textbufl.get_end_iter()
    #ctag = self.textbufl.create_tag( "color", foreground="#FFFF00") 
    ctag = self.textbufl.create_tag( "color", foreground="#EE1BEC") 
    self.textbufl.insert_with_tags(position,"En nu wat gekleurde tekst",ctag)
    position=self.textbufr.get_end_iter()
    self.textbufr.insert(position, "een beetje normale text\n op 2 regels\n")
    """
    #==== final (show) ===
    self.window.add( self.mainbox)
    self.window.show_all()
  def main(self):
    Gtk.main()

  def on_button_clicked(self,b):
    print('butt klik')

  def tappend(self, texbuf, astring, col=None):
    pos=texbuf.get_end_iter()
    if col==None:
      texbuf.insert(pos,astring)
    else:
      texbuf.insert_with_tags(pos,astring,col)

  def showdiff(self,fsa,fsb):
    #seqm=difflib.SequenceMatcher(None,fsa, fsb)
    seqm=difflib.SequenceMatcher(lambda x: x in ' \t\n',fsa, fsb)
    for opcode, a0, a1, b0, b1 in seqm.get_opcodes():
      if opcode == 'equal':
        self.tappend(self.textbufl, seqm.a[a0:a1])
        self.tappend(self.textbufr, seqm.b[b0:b1])
        #print('eq : ',a0,a1)
      elif opcode == 'insert':
        self.tappend(self.textbufr, seqm.b[b0:b1],self.rtag)
        #print('ins: ',b0,b1)
      elif opcode == 'delete':
        self.tappend(self.textbufl,seqm.a[a0:a1], self.ltag)
        #print('del: ',a0,a1)
      elif opcode == 'replace':
        #print('replace: ',a0,a1,b0,b1, seqm.a[a0:a1],' -> ', seqm.b[b0:b1])
        self.tappend(self.textbufl, seqm.a[a0:a1], self.ltag)
        self.tappend(self.textbufr, seqm.b[b0:b1], self.rtag)

def readfile(fn):
  try:
    f=open(fn,'r')
    ft=f.readlines()
    fs=''.join(ft)
  except IOError:
    print('Can not read ',fn)
    exit(1)
  return fs

def getfile(n):
  fn=sys.argv[n]
  if not os.path.isfile(fn):
    print('Argument should be a file !: ',fn)
    sys.exit(1)
  return readfile(fn)

if __name__ == "__main__":
  if sys.version[0] != '3':
    print("version", sys.version, sys.version[0], type(sys.version[0]))
    print("Error: Python version >=3 is required.")
    sys.exit(1)

  if len(sys.argv)<3:
    print('geef 2 file namen')
    exit(1)
  fsa=getfile(1)
  fsb=getfile(2)

  m = CompareText( "Compare Text",fsa,fsb)
  m.main()
  sys.exit(0)