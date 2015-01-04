#!/usr/bin/env python
"""Program to compare 2 directories v0.752
Show files that are different and copy or delete those differences.
Author: Henk Speksnijder october 2013.
"""

#========== S E T U P -- B A S E ==================================================================
import sys, os, subprocess
import threading
from os.path import join, getsize, exists
from shutil import copy2
try:
  import gi
  gi.require_version('Gtk', '3.0')  # tell we want GTK3
except ImportError:
  print('You need to install python-gobject.')
  sys.exit(1)

try:
  from gi.repository import Gtk, GObject   # pylint: disable=E0611
except ImportError:
  print("You need to install python-Gobject or GTK3", end=" ")
  print("or set your PYTHONPATH correctly.")
  print("try: export PYTHONPATH=", end=" ")
  print("/usr/lib/python3.2/site-packages/")
  sys.exit(1)
  # now we have both gtk and Gtk.glade imported and run GTK v3

def extprocess(cmd):
  """Start subprocess with cmd and return the output string."""
  sproc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
  outmsg, _ = sproc.communicate()
  return outmsg.decode()  # pylint: disable=E1101

def extprogram(prog):
  """Check we have an excecutable program in our Path."""
  msg = extprocess(["which", prog])
  if msg[7:9] == "no":
    return False
  return True

def findmyutils():
  """Check we have utilities to compare text and to compare images.
  Return the right program names.
  """
  def localutil(programname):
    """Combine local program path with programname to form a locat utility."""
    gladedir = os.path.dirname(os.path.realpath(__file__))
    localutil = join(gladedir, programname)
    return localutil

  def testlocal(programname):
    """Return if the programname is in the local folder."""
    return os.path.isfile(localutil(programname))

  def testlist(testlist):
    """test various names from testlist"""
    for tu in testlist:
      if testlocal(tu):
        util = localutil(tu)
    for tu in textutil:
      if extprogram(tu):
        util = 'comparetext'
    return util

  # ctu = compare text utility
  # ciu = compare image utility
  textutil = ['comparetext', 'comparetext.py']
  imageutil = ['compareimage', 'compareimage.py']
  ctu = testlist(textutil)
  ciu = testlist(imageutil)
  return ctu, ciu

#========== GUI -- C L A S S -- D E F I N I T I O N ==============================================

class different(Gtk.Window):
  """Create a main window to display files in a master and a slave directory.
  Create buttons to delete or copy files around.
  """
  def __init__(self, ctu, ciu):
    """init and display the main window"""
    def __boxbutton(boxwg, labeltxt, callbackfun):
      """Local function to setup a button + callback into a box"""
      newbut = Gtk.Button(label=labeltxt)
      newbut.connect("clicked", callbackfun)
      boxwg.pack_start(newbut, False, True, 0)
      return

    Gtk.Window.__init__(self)   #, title="CompareDir")
    self.comparetextutil = ctu
    self.compareimageutil = ciu
    self.fileprocess = 'none'

    #---- middele pane with most buttons:
    self.box8 = Gtk.Box()
    __boxbutton(self.box8, "Diff", self.process_diff)
    __boxbutton(self.box8, "Equal", self.process_eq)
    __boxbutton(self.box8, "All", self.process_all)
    self.progresf = self.__progressbar("File Processing")
    self.progresd = self.__progressbar("Directory Processing")
    self.box7 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    self.box7.pack_start(self.progresd, False, True, 0)
    self.box7.pack_start(self.box8, False, True, 0)
    self.box7.pack_start(self.progresf, False, True, 0)
    __boxbutton(self.box7, "Copy to Slave", self.copytos_click)
    __boxbutton(self.box7, "Copy to Master", self.copytom_click)
    __boxbutton(self.box7, "Delete from Slave", self.deletes_click)
    __boxbutton(self.box7, "Delete from Master", self.deletem_click)
    __boxbutton(self.box7, "Compare Files", self.comparef_click)
    self.box3 = Gtk.Box()   # Copy/Delete/Compare Buttons
    self.box3 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    self.message = Gtk.Label("...")

    #----- left hand pane with master dir
    self.bmdir = Gtk.Button("Master Directory")
    self.bmdir.connect("clicked", self.bmdir_click)
    #self.viewmdir = Gtk.Entry(hexpand=True, halign=Gtk.Align.START)
    self.viewmdir = Gtk.Entry(hexpand=True, halign=Gtk.Align.FILL)
    self.treeviewm = Gtk.TreeView()
    self.scrolled1 = Gtk.ScrolledWindow()
    self.scrolled1.add(self.treeviewm)
    self.scrolled1.set_vexpand(True)

    #----- right hand pane with slave dir
    self.bsdir = Gtk.Button("Slave Directory")
    self.bsdir.connect("clicked", self.bsdir_click)
    #self.viewsdir = Gtk.Entry(hexpand=True, halign=Gtk.Align.START)
    self.viewsdir = Gtk.Entry(hexpand=True, halign=Gtk.Align.FILL)
    self.treeviews = Gtk.TreeView()
    self.scrolled2 = Gtk.ScrolledWindow()
    self.scrolled2.add(self.treeviews)

    #----- Now put all together in a grid in a window
    self.grid0 = Gtk.Grid()         # X  Y  W  H
    self.grid0.attach(self.bmdir,     0, 0, 1, 1)
    self.grid0.attach(self.viewmdir,  1, 0, 1, 1)
    self.grid0.attach(self.message,   2, 0, 1, 1)
    self.grid0.attach(self.bsdir,     3, 0, 1, 1)
    self.grid0.attach(self.viewsdir,  4, 0, 1, 1)
    self.grid0.attach(self.scrolled1, 0, 1, 2, 1)
    self.grid0.attach(self.box7,      2, 1, 1, 1)
    self.grid0.attach(self.scrolled2, 3, 1, 2, 1)

    self.window = Gtk.Window()
    self.window.set_title('Compare Directories')
    self.window.connect("delete-event", Gtk.main_quit)
    self.window.add(self.grid0)  # note window can only contain 1 item
    self.__add_columns(self.treeviewm)
    self.__add_columns(self.treeviews)
    self.window.show_all()
    self.viewmode = 'a'  # sane default to avoid crash over missing var
    return

  def __progressbar(self, text):
    """convinence function to create progress bar with a text on top."""
    pbar = Gtk.ProgressBar()
    pbar.set_fraction(0)
    pbar.set_show_text(True)
    pbar.set_text(text)
    return pbar

  def __add_columns(self, treeview):
    """Convinence function to add columns, Note:
    column for File name is resizable
    column for File size is resizable
    column for subdirectory NOT resizable
    """
    columndef = (("Filename", True),
                 ("Filesize", True),
                 ("subdirectory", False))
    for i, col in enumerate(columndef):
      column = Gtk.TreeViewColumn(col[0], Gtk.CellRendererText(), text=i)
      column.set_sort_column_id(i)
      column.set_resizable(col[1])
      treeview.append_column(column)
    tvs = treeview.get_selection()      # the selection-object of the treeview
    tvs.set_mode(Gtk.SelectionMode.MULTIPLE)	 # allow to select multiple rows
    return

  #----- C A L L -- B A C K S -- D I R E C T O R Y & P R O C E S S--------------------------------
  # m = master en s = slave
  # b = button en v = view text box

  def bmdir_click(self, widget):
    """Set the master directory"""
    self.viewmdir.set_text(self.__choose_dir())
    return

  def bsdir_click(self, widget):
    """Set the slave directory"""
    self.viewsdir.set_text(self.__choose_dir())
    return

  #-------------- Support functions --------

  def __choose_dir(self):
    """Open a window to select a directory, Return directory"""
    print('choose self type: ', type(self))
    dialog = Gtk.FileChooserDialog(
        "Choose Directory",
        self,
        Gtk.FileChooserAction.SELECT_FOLDER,
        (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
         Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
    if (dialog.run() == Gtk.ResponseType.OK):
      adirname = dialog.get_filename()
    else:
      adirname = ""   # Closed, no files selected
    dialog.destroy()
    return adirname

  def __getdirs(self):
    """Return masterdirectory and slavedirectory."""
    md = self.viewmdir.get_text()
    sd = self.viewsdir.get_text()
    dirok = False
    if md == "":
      self.__warning_dialog("First you need to select a Master Directory")
    elif sd == "":
      self.__warning_dialog("You need to select a Slave Directory")
    else:
      dirok = True
    return (dirok, md, sd)

  def __process_func(self, widget, comparemode):
    """Process Directories and select files using a function
    comparecode 'a' = All, 'd' = Different, 'e' = Equal
    """
    mestext = {
        'a': 'show all files',
        'd': 'different files',
        'e': 'show equal files'}
    dirok, mdir, sdir = self.__getdirs()
    if dirok:
      self.message.set_text(mestext[comparemode])
      self.viewmode = comparemode
      #----------Threaded function----------
      dpt = dirprocessthread(mdir, sdir,
                             comparemode,
                             self.progresd.set_fraction,
                             self.updateview)
      dpt.start()
      #----------Threaded function END-------
    return

  def updateview(self, lijstm, lijsts):
    """Callback to update the master and slave views."""
    self.treeviewm.set_model(lijstm)  # attach list to the view to make it visible
    self.treeviews.set_model(lijsts)  # attach list to the view to make it visible
    self.progresd.set_fraction(0)
    return

  #---------- C A L L B A C K S ---------- ALL -- DIFFERENT -- EQUAL ----------
  def process_all(self, widget):
    """process Directories and get ALL files."""
    self.__process_func(widget, 'a')

  def process_diff(self, widget):
    """Process Directories and get files different on both sides"""
    self.__process_func(widget, 'd')

  def process_eq(self, widget):
    """Process directories and get files equal on both sides"""
    self.__process_func(widget, 'e')

  #---------- C A L L B A C K S ----- COPYM--COPYS--DELETEM--DELETES--COMPARE---
  # m=master en s=slave
  def copytos_click(self, widget):
    """copy selected files to Slave.
    """
    if self.viewmode == 'e':
      self.__warning_dialog("File already exist in Slave")
    else:
      self.fileprocess = 'cs'
      fpnlist, dirlist = self.__selectfilelist('m')
      if self.__selectlistcheck(fpnlist, "copy"):
        fct = threading.Thread(target=filescopythread,
                               args=(fpnlist,
                                     dirlist,
                                     self.progresf.set_fraction,
                                     self.updatedm,
                                     self.__warning_dialog)
                               )
        fct.start()
    return

  def copytom_click(self, widget):
    """copy selected files to Master.
    """
    if self.viewmode == 'e':
      self.__warning_dialog("File already exist in Master")
    else:
      self.fileprocess = 'cm'
      fpnlist, dirlist = self.__selectfilelist('s')
      if self.__selectlistcheck(fpnlist, "copy"):
        fct = threading.Thread(target=filescopythread,
                               args=(fpnlist,
                                     dirlist,
                                     self.progresf.set_fraction,
                                     self.updateds,
                                     self.__warning_dialog)
                               )
        fct.start()
    return

  def updateds(self, status):
    """Callback to update the slave view."""
    self.progresf.set_fraction(0)
    if status:  # The thread went ok we can update the gui:
      model, tilist = self.__tvselection(self.treeviews)
      for ti in tilist:
        model.remove(ti)  # delete row i of the model
    else:
      self.__process_func(None, self.viewmode)
    return

  def updatedm(self, status):
    """Callback to update the master view."""
    self.progresf.set_fraction(0)
    if status:  # The thread went ok we can update the gui:
      model, tilist = self.__tvselection(self.treeviewm)
      for ti in tilist:
        model.remove(ti)  # delete row i of the model
    else:
      self.__process_func(None, self.viewmode)
    return

  def __tvselection(self, tv):
    """Return the list of selected (iters) in treeview tv"""
    til = []
    tvz = tv.get_selection()              # get from treeview the selection-object
    tm, splist = tvz.get_selected_rows()  # tm=tree model , splist = list of selected paths
    splist.reverse()					    # set in the right order for deletion
    for sp in splist:
      til.append(tm.get_iter(sp))
    return tm, til

  def __selectfilelist(self, mode):
    """Return a list of selected files in treeview tv"""
    fpnlist = []
    dirlist = []
    if mode == 'm':
      ad = self.viewmdir.get_text()  # get master dir
      bd = self.viewsdir.get_text()  # get slave dir
      tm, tilist = self.__tvselection(self.treeviewm)
    else:
      bd = self.viewmdir.get_text()  # get master dir
      ad = self.viewsdir.get_text()  # get slave dir
      tm, tilist = self.__tvselection(self.treeviews)
    for ti in tilist:					       # ti = tree iter to selected item
      subdir = tm.get_value(ti, 2)
      bestand = join(ad, subdir[1:], tm.get_value(ti, 0))	 # glue master subdir and filenaam
      targetdir = join(bd, subdir[1:])  # glue slave subdir and filenaam
      fpnlist.append(bestand)
      dirlist.append(targetdir)
    # note: JOIN has a nasty habit: when subdir starts with '/' than it assumes
    # that it's an absolute path and ignores md. So i skip the first char with [1:]
    return fpnlist, dirlist

  def __selectlistcheck(self, fpnlist, wtext):
    """Take action to deal with suspect list length."""
    count = len(fpnlist)
    if count < 1:
      self.__warning_dialog("No files Selected")		# nothing selected
      ret = False
    elif count == 1:
      ret = True
    elif count > 1:							# Warn user about many files
      #HERE IS A BUG
      ret = self.__warning_dialog("Shure you want to %s :%u files ?" %(wtext, count))
    return ret

  def deletem_click(self, widget):
    """Delete selected files from master."""
    self.fileprocess = 'dm'
    fpnlist, zz = self.__selectfilelist('m')
    if self.__selectlistcheck(fpnlist, "delete"):
      fdt = threading.Thread(target=filesdelthread,
                             args=(fpnlist,
                                   self.progresf.set_fraction,
                                   self.updatedm,
                                   self.__warning_dialog)
                             )
      fdt.start()
    return

  def deletes_click(self, widget):
    """Delete selected files from slave."""
    self.fileprocess = 'ds'
    fpnlist, zz = self.__selectfilelist('s')
    if self.__selectlistcheck(fpnlist, "delete"):
      fdt = threading.Thread(target=filesdelthread,
                             args=(fpnlist,
                                   self.progresf.set_fraction,
                                   self.updateds,
                                   self.__warning_dialog)
                             )
      fdt.start()
    return

  #--------- Helper functions & select_action ----------------
  def __copyitem(self, fdn, subdir, maindir):  # pylint: disable=C0111
    fulldir = join(maindir, subdir[1:])
    result = True
    try:
      if not exists(fulldir):  # make sure the destination directory exist
        os.makedirs(fulldir)
      copy2(fdn, fulldir)
    except OSError:
      self.__warning_dialog("Error copy file %s to %s" %(fdn, subdir))
      result = False
    return result

  def __updategui(self, modeldest, model, i):  # pylint: disable=C0111
    if self.viewmode == "a":
      modeldest.append([model[i][0], model[i][1], model[i][2]])
    if self.viewmode == "d":
      model.remove(i)  # delete row i of the model
    return

  def __deleteitem(self, fdn):
    """Delete file, fdn = file directory + name."""
    result = True
    try:
      os.remove(fdn)				# delete file
    except OSError:
      result = self.__warning_dialog("Error to remove file %s" %(fdn))
    return result

  def __select_action(self, tm, i, mode, m2):
    """Parameters: treemodel, path, iter, target, second-model."""
    subdir = tm.get_value(i, 2)
    md = self.viewmdir.get_text()  # get master dir
    sd = self.viewsdir.get_text()  # get slave dir
    bestandm = join(md, subdir[1:], tm.get_value(i, 0))	 # glue master subdir and filenaam
    bestands = join(sd, subdir[1:], tm.get_value(i, 0))  # glue slave subdir and filenaam
    # note: JOIN has a nasty habit: when subdir starts with '/' than it assumes
    # that it's an absolute path and ignores md. So i skip the first char with [1:]
    result = "ok"
    if mode == "ms":
      result = self.__copyitem(bestandm, subdir, sd)
      self.__updategui(m2, tm, i)
    elif mode == 'sm':
      result = self.__copyitem(bestands, subdir, md)
      self.__updategui(m2, tm, i)
    elif mode == "dm":
      result = self.__deleteitem(bestandm)
      tm.remove(i)
    elif mode == "ds":
      result = self.__deleteitem(bestands)
      tm.remove(i)
    return result				# in case of error return what the user want: "Cancel"=False
    # remark, note, comment:
    # Actually we have to consider 6 different cases:
    # The setting could be (treeview) : different, equal of all files
    # And we have buttons for "copy" or "delete"
    # and that makes a total of 2*3:
    # treeview	dif	equal	all
    # setting
    # 	copy	X	Z	C
    #	delete	X	X	X
    #
    # where
    #	X = remove item from the treeview
    #	Z = useless, impossible,
    #	 	catch this at the begining of copy_tos
    #	C = copy item to other treeview

  def comparef_click(self, widget):
    """compare 2 textfiles or 2 images.
       if user selected 1 file on master and 1 on slave.
       if user selected more than 1 file in master or slave: Quit.
    """
    txtext = ['.c', '.C', '.cpp', '.CPP', '.cxx', '.CXX', '.h', '.H',
              '.html', '.HTML', '.json', '.JSON', '.txt', '.TXT',
              '.pas', '.PAS', '.po', '.PO', '.py', '.PY']
    imageext = ['.jpg', '.png', '.bmp', '.JPG', '.PNG', '.BMP']

    def selectcount(treeview):
      """Return number of selected files from the view."""
      tvs = treeview.get_selection()
      return tvs.count_selected_rows()

    def selectitem(treeview):
      """Return one selected file from the view."""
      tvs = treeview.get_selection()
      tm, splist = tvs.get_selected_rows()
      tmiter = tm.get_iter(splist[0])
      subdir = tm.get_value(tmiter, 2)
      fn = tm.get_value(tmiter, 0)
      return join(subdir[1:], fn)

    mcount = selectcount(self.treeviewm)
    scount = selectcount(self.treeviews)
    if (scount < 1) or (mcount < 1):
      self.__warning_dialog("No files Selected.")
    elif (scount > 1) or (mcount > 1):
      self.__warning_dialog("To many files Selected, need 1 left and 1 right.")
    else:
      md = self.viewmdir.get_text()  # get master dir
      sd = self.viewsdir.get_text()   # get slave dir

      fnm = join(md, selectitem(self.treeviewm))		# glue master subdir and filenaam
      fns = join(sd, selectitem(self.treeviews))		# glue slave subdir and filenaam
      #print('master: ', fnm, ' slave: ', fns)
      # Now we have all required parts lets FLY:
      fextm = os.path.splitext(fnm)[1]
      fexts = os.path.splitext(fns)[1]
      if (fexts != fextm):
        self.__warning_dialog('Files are Different ! '+ fextm+ ' <> ' +fexts)
      elif (fextm in txtext) and comparetextutil is not None:
        cmd = [comparetextutil, fnm, fns]
        extprocess(cmd)
        #print(extprocess(cmd)) DEBUG
      elif (fextm in imageext) and compareimageutil is not None:
        cmd = [compareimageutil, fnm, fns]
        extprocess(cmd)
        #print(extprocess(cmd)) DEBUG
      else:
        self.__warning_dialog('No utility to compare files type: ' + fextm + ' - ' +fexts)
    return

  def __warning_dialog(self, amessage):    # pylint: disable=C0111
    dialog = Gtk.MessageDialog(
        self,
        Gtk.DialogFlags.DESTROY_WITH_PARENT,
        Gtk.MessageType.WARNING,
        Gtk.ButtonsType.OK_CANCEL,
        amessage)
    if (dialog.run() == Gtk.ResponseType.OK):
      res = True
    else:
      res = False
    dialog.destroy()
    return res

#===== THREAD FILES ========================================New 20131021

def filesdelthread(fpnlist, guibar, guiview, guiwarn):
  """Delete all files according to fpnlist"""
  nr = len(fpnlist)
  status = True
  for i in range(nr):
    fpn = fpnlist[i]
    try:
      os.remove(fpn)  # delete file
      #print('Deleted: ', fpn)   DEBUG
    except OSError:
      GObject.idle_add(guiwarn, 'Error to remove file '+fpn)
      status = False
      break
    GObject.idle_add(guibar, float(i)/nr)
  GObject.idle_add(guiview, status)

def filescopythread(fpnlist, dirlist, guibar, guiview, guiwarn):
  """Copy all files in fpnlist to directries in dirlist."""
  status = True
  if len(fpnlist) != len(dirlist):
    status = False
  else:
    nr = len(fpnlist)
    for i in range(nr):
      fpn = fpnlist[i]
      targetdir = dirlist[i]
      try:
        if not os.path.isdir(targetdir):  # make sure the destination directory exist
          os.makedirs(targetdir)
          #print('made dir: ', targetdir)
        copy2(fpn, targetdir)
        #print('copyd: ', fpn, targetdir)
      except OSError:
        GObject.idle_add(guiwarn('Error copy file ' +fpn +' to '+ targetdir))
        status = False
        break
      GObject.idle_add(guibar, float(i)/nr)
  GObject.idle_add(guiview, status)
  return

#===== THREAD DIR ==========================================New 20131016

class dirprocessthread(threading.Thread):
  """All boilerplate to process the directories in a separate thread."""

  def __init__(self, mdir, sdir, mode, guicbbar, guicbview):
    """Init"""
    threading.Thread.__init__(self)
    self.mdir = mdir
    self.sdir = sdir
    self.listm = Gtk.ListStore(str, int, str)
    self.lists = Gtk.ListStore(str, int, str)
    self.mode = mode
    self.guicbbar = guicbbar
    self.guicbview = guicbview

  def run(self):  # dirprocess
    """Read Dirs and select files using a function
    comparecode 0 = All, 1 = Different, 2 = Equal
    """
    def selectal(aitem, alist):  # pylint: disable=C0111
      return True

    def selectdf(aitem, alist):  # pylint: disable=C0111
      return not(aitem in alist)

    def selecteq(aitem, alist):  # pylint: disable=C0111
      return aitem in alist

    func = {  # dirpocess
        'a': selectal,
        'd': selectdf,
        'e': selecteq}

    def dirlistfiles(directory):  # dirpocess
      """Search all files of directory and Retrun a list."""
      dirlist = []
      for root, dirs, files in os.walk(directory):
        for name in files:
          fz = getsize(join(root, name))
          # skip the first part of root since it is same as'directory'
          dirlist.append([name, fz, root[len(directory):]])
      return dirlist

    def createmodel(dirlist, dirlist2, compfunc):  # dirpocess
      """Use comparefunction to select return files."""
      lstore = Gtk.ListStore(str, int, str)
      for row in dirlist:
        if compfunc(row, dirlist2):
          lstore.append(row)
      return lstore

    mfiles = dirlistfiles(self.mdir)  # get a list with all files of directory mdir
    GObject.idle_add(self.guicbbar, 0.3)
    sfiles = dirlistfiles(self.sdir)  # get a list with all files of directory sdir
    GObject.idle_add(self.guicbbar, 0.6)
    self.listm = createmodel(mfiles, sfiles, func[self.mode])  # filter
    GObject.idle_add(self.guicbbar, 0.8)
    self.lists = createmodel(sfiles, mfiles, func[self.mode])  # filter
    GObject.idle_add(self.guicbbar, 0.95)
    GObject.idle_add(self.guicbview, self.listm, self.lists)
    return

#========== M A I N ===============================================================================

if __name__ == "__main__":
  # find the utility programs
  comparetextutil, compareimageutil = findmyutils()
  # start application
  GObject.threads_init()  # new 20131016 threading
  app = different(comparetextutil, compareimageutil)
  Gtk.main()
  sys.exit(0)

#========== COMMENT ===============================================================================
#---------- Verschildir Version Summary -----------------------------------------------------------
# Verschildir: a program to compare directories using Python2 and Gtk2
# v1  28 Oct. 2007 initial work on the GUI, learning glade and pygtk.
# v2   9 Nov. 2007 add more code to get a working program.
# v3  12 Nov. 2007 lot's of code changes to create the 'delete' buttons.
# v4  18 Nov. 2007 add image on 2 buttons (attempt to make the interface look icer)
#         + debuuging: add extra code to process path & filenames properly.
# v5  25 Nov. More work on fucntions to copy/delete and master/slave.
# v6   2 dec. Need to add code to update the GUI depending on view all/eq/diff.
# v7  24 Feb. When i moved this program to another computer: cannot find glade file.
#             Had to add code to assist in finding it's glade file.
# v8  29 Apr. 2012 Add code to detect if target directory exist, when not than create it.
#---------- CompareDir Version Summary ------------------------------------------------------------
# CompareDir is a new name using Python3 + pygobject + Gtk3, Version count reset at Zero:
# v00   2 may 2012 gtk2 -> gtk3 automated conversion using pygi-convert.sh
#         plus: some manual code cleanup, plus made english name & source comment.
#         create a new glade file compatible with python3 & Gtk3.
# v01   2 may 2012 Debugging & code changes due to the move to Python3 Gtk3.
# v02   2 may 2012 Debugging & code changes due to the move python2/gtk2 - Python3 Gtk3.
# v03   4 may 2012 improve the .glade file to get the button images there again.
# v04   5 may 2012 Some improvements to the .glade file te get resizing work properly.
# v05   6 may 2012 Improve the search for the gladefile
#       and improve error message when gladefile not found.
#       This is the first released to Sourceforge.
# v06  23 sept. Add button & extra code to compare 2 textfiles (experimental).
# v061 24 sept. Add code to the new button, quite complex as we can compare files 1:1
#       so we have to check user selected only 1 file on left and 1 on right.
#       Than we struggle with Gtk tree iters to get the actual filnames.
#       9 march to 29 sept. 2013 work on the tool to compare textfiles.
#       9 march to 13 oct. 2013 work on the tool to compare image files using python pilows.
# v062 Using pylint and pep8 reveals my code is rather sloppy hence lots of small changes.
#       Add code to actually find the utils (compare text / compare image).
# v063 Changed behaviour of pylint and pep8 using pylintrc and tox.ini to better match my needs.
#       Various changes to try reduce program complexity.
# v064 Again attempt code improvements.
# v065 Again code improvements, embed some pylint instructions in the source
#       like "#Pylint: disable=C0111" greatly improves matters:
#       Some warnings i don't like to disable completely but are not always useful.
#       My work with pep8 and pylint made me detect various sloppy details in the code
#       and to make it more adhere to standards thus make it more easy to read.
# v066 7 oct. 2013 A few small improvements.
# v07  13 oct. 2013 improvements & debugging to compare 2 files.
#       This is the second released to Sourceforge.
# v071 Try to leave the glade file and build the GUI with statements.
#       Advantage: don't need to search or to worry if we find the glade file.
#       the gladefile=18 kByte while the extra code is less than 3 kByte.
# v072 Attempt to build a toolbar: turns out it's ugly and not very useful.
# v073 Experiment with toggle button for diff/eq/all: not good.
#       Change Gtk.Box (depracated) to Gtk.Grid (more modern and less lines of code).
#       Add progress bars.
# v074 Remove toggle buttons.  Try to update a progressbar.
#       Deleted obsolete code lines with Gtk.Box and Toolbar
#       Note progressbar can NOT work because i have only 1 thread !!
#       Need to read the documentation to implement a multithread python program.
# v075 Ok, done some reading and this is a first threading attempt.
# v076 Need to review and modify a lot of code to make it multithreading,
#       because my old code had data-processing and GUI updates completely mixed.
#       New time consuming thread (read dirs) should not update the GUI.
# v077 The threading seems to work, now code cleanup.
# v078 GUI improvements using Gtk.Grid / hexpand / halign and a function to create buttons.
# v079 reduce GUI code with a function to add buttons to a Gtk.Box
#       change '_clicked' to '_click' to make callback functioncall shorter.
# v080 Design Thread for file processing: copy or delete.
#       And a lot of code changes to separate GUI from processing the files.
# v081 For copy need to make some functions more useful / generic.
#       Some code cleanup. Reduce code complexity in filescopythread.
# v082 Remove some print statements (annoying 'noise' to the terminal)
#       Annoying bug: copy multiple files gives annoying bug in warningbox.
#       Remove some more obsolete code.
# v083 28 Oct. 2013 Annoying bug repaired.  Final code cleanup. 
# v084 20140427 Add extra comment on the versions progress.
# v084 20140427 line 89 added: Gtk.Window.__init__(self)
#       After an update on some libraries now we get errors 
#       from Line 197 dialog = Gtk.FileChooserDialog(
#       seems the link to the window was missing.
# v086 20150102 change viewmdir/viewsdir to expand with the window:
#       Gtk.Entry: halign=Gtk.Align.START => Gtk.Align.FILL
#
# Lines of source code summary:
# v0.5    224   base.
# v0.6    234   compare 2 text files (experimental).
# v0.7    316   compare 2 text/image files.
# v0.71   364   because glade file removed.
# v0.8    521   because multithreading
# v0.83   478   code cleanup

# Remove code duplication
#    section with All/Diff/Eq from 86 to 50 lines.
# Make program structure simpler
#    change 2 globals to class parameters
#    avoid global vars by using parameters in class __init__
#    select_action reduce complexity by using procedures
# Version 20131014 remove gladefile and put everything into python.
#    This avoids any search or doubt about the glade file.
#    And we have less lines of code:
#    program + glade file was 17k+17k
#    program with buildin gui data is 17k
#========= BOX vs GRID ============================================================================
# https://developer.gnome.org/gtk3/3.4/ch28s02.html
#-----------BOX----------
# When adding a child to a GtkBox, there are two parameters (child properties)
# expand and fill that determine how the child size behaves in the main direction
# of the box. If expand is set, the box allows the position occupied by the child
# to grow when extra space is available. If fill is also set, the extra space is
# allocated to the child widget itself. Otherwise it is left 'free'. There is no control
# about the 'minor' direction; children are always given the full size in the minor
# direction.
#-----------GRID-----------
# GtkGrid instead, fully supports the new "hexpand", "vexpand", "halign"
# and "valign" properties. The "hexpand" and "vexpand" properties operate
# similar to the expand child properties of GtkBox. As soon as a column contains a
# hexpanding child, GtkGrid allows the column to grow when extra space is available
# (similar for rows and vexpand). In contrast to GtkBox, all the extra space is
# always allocated to the child widget, there are no 'free' areas.
#======== Button Code reduction ===================================================================
# When a button is made of only a Label and a Callback
# than we can reduce the sourcecode even further, replace this:
#    self.buttoncs = Gtk.Button(label="Copy to Slave")
#    self.buttoncs.connect("clicked", self.copytos_clicked)
#    self.box7.pack_start(self.buttoncs, False, True, 0)
# with this on-liner:
#    boxpack(self.box7, "Copy to Slave", self.copytos_clicked)
# Plus a function:
# def boxpack(self, boxwg, labeltxt, callbackfun)
#    newbut = Gtk.Button(label=labeltxt)
#    newbut.connect("clicked", callbackfun)
#    boxwg.pack_start(self.newbut, False, True, 0)

