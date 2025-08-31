# Advanced-Deduplication
Deduplicates directories in a reversible manner.

#Simple Guide
First download Python https://www.python.org/downloads
Make sure you have the modules I use (Python comes with pre-installed modules so it might not be needed)

Modules I used:
  import tkinter as tk
  from tkinter import ttk, filedialog, messagebox, scrolledtext
  import os
  import datetime
  import threading
  from pathlib import Path
  from typing import List
  import queue
  import json
  import shutil
  from typing import Dict, List, Optional, Tuple
  import hashlib
  from typing import List, Dict, Set, Tuple, Optional
  from collections import defaultdict

Launch the program by double clicking on GUI.py file

#Fuctionality
The program reorganizes the folder structures in order to reduce the plain size of the directory when compressed, and deduplicates extensivly.

The logic behind the program:

Phase 1, Folder Treatment
Two similar directories are located on the same directory, for
reference named:
-"Make.Waffles.12"
-"Make.Windows.25"

To make the paths to the directories compact, we would first make a
folder named after the two directories why try to compare which for
our example is the name "Make.W" and inside we will put the
directories we try to compare. Next we will rename the directories
into the following:
- "affles.12"
- "indows.25"

When we want to reverse it, we would copy the name of the folder
and paste it on the front of the name of the compared directories.

Phase 2, File treatment
We need to compare the files and remove duplicates in a reversible
maner.

To do this we would make a directory named for reference "Base Files"
and inside it we would copy all the duplicate directories or files exactly
as they are. Then deletion of the initial duplicate files would follow only
inside the "affles.12", "indows.25". Base Files is known to contain our
duplicates generally speaking in my manual implementations of this logic.

Phase 3, Scalling Number of Compared Directories
To take proper advantage of the program we must have a scalling
number of the directories we compare so that we can compare more than
two directories at the same time. This way we make one more example
for if we introduced e.g. another two folders for reference named:
-"Make.Webs.124" -"Make.Wine.102"

which after processing would turn into:
-"ebs.124"
-"ine.102"

Now say that "Base Files" folder of "ine.102" and "ebs.124" have
duplicates with the "Base Files" folder of the "affles.12" and
"indows.25". We will have to make a new "Base Files" folder in order
to adress deduplication in this case. This would scale up.
