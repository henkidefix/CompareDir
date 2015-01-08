CompareDir v0.86

Did you ever copy many files to a portable usb-harddisk and use another 
system to update or delete files ? And later have trouble to 
find the few files you changed among many others ?
CompareDir does just that: it can compare 2 directories + subdirectories and you decide what files you want to keep, copy or delete.
Manual: point it at a MasterDir, a SlaveDir than
click "Diff" = show only the files that are available in only 1 directory-tree.
Or click "All" = show all files in both directories.
Or click "Eq" = show file only the files that are the same.
Note the program cheqs FileName, FileSize, FileDate and (sub)directory. It does not compute md5 sums because that would make it extremely slow. Mind you i use this regular for directories with 2000 photos.
Based on Python, pygobject and gtk3.
No installation:
untar -xvzf CompareDir.tgz
where you want and run.

Latest update to v0.86:
To avoid errors with locating the glade file added code
to build the gui with python. Got rid of the gladefile.
Added progress bar. Than learned this can only work on
a multithreaded application. Never done that before
so after some learning this is now using treading.
Some minor improvements over v0.83.

Features:
    Small program.
    Easy to use.
    Can work Local or with USB disk or over your local network.
    No installation: Save somewhere, untar, and run.
    Few dependencies (python3 & pygobject & gtk3)
    Compare 2 text files
    Compare 2 images (using python-pillow)
    Progressbar.

Roadmap: 
    Add languages (german, dutch, french ?) 
    change to show the files in a directory tree ? 
      (is more like the regular user expectation?) 
    Add a help-screen ? Add keyboard shortcuts ? 
    Rewite in fpGUI+FreePascal for speed improvement ? 

Henk Speksnijder  3 january 2015
![screenshot](https://cloud.githubusercontent.com/assets/10391134/5668156/cd3f26fa-976d-11e4-844e-e3198753b3d0.png)
