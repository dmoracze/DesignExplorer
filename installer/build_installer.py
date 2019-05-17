#! /usr/bin/env python
from datetime import datetime
from jkpy import *
import re
import sys
import os

# script to build the DesignExplorer installer.  Only works on Josh's computer for convenience


# installed program folders and files of interest
'''
~
    DesignExplorer (copied in, executable launcher for the user, just runs internal_launcher.sh)
    
    .DesignExplorer (app folder, created as needed)
        default_project (not to be modified by installer, is currently created by the program if user doesn't want to specify a path for a project)
        bin
            licenses (folder, made and relevent files copied in as needed)
            internal_launcher.sh (copied in, sets a few environment variables to get started, then runs internal_launcher.py)
            internal_launcher.py (copied in, finally starts the actual program)
            3dDeconvolve (downloaded from AFNI servers)
            miniconda2 (installed)
                bin
                    conda
                    python
                lib
                    python2.7
                        site-packages
                            jkpy (copied in)
                            DesignExplorer (copied in)
'''
'''
installation process:
    * make a temp folder wherever the user is running things from
    * extract payload into that folder
        installation and launcher scripts
        jkpy folder
        DesignExplorer folder
        licenses
    * run the main installation script (copies things where they need to go, etc)
    * delete the temp folder
'''

#impl: documentation distribution, and integration with the GUI

#idea: versioning?  simple just by date?
# should be in the GUI somewhere, an about menu or something.
#version=datetime.now().strftime('%Y-%m-%d--%H%M')


# convenient version for Josh
if len(sys.argv)==1:
    jkpy_parent = '/home/Josh/Dropbox/bin/TOOLBOX'
    de_parent = '/home/Josh/Dropbox/DesignExplorerRewrite'
    opath = '/home/Josh/InstallDesignExplorer'
# flexible version
else:
    (jkpy_parent, de_parent, opath) = sys.argv[1:]


'''
I tried to save output automatically using tee, but either tee or the stream
redirection caused the fancy output updating (progress bars) to flood the screen.
Surely users can run in a terminal if they haven't already and copy the messages
if there is a problem.  
'''
    
#fixme: why does this work without marking install.sh as executable?  Does it?
extractor='''#! /bin/bash
SKIP=`awk '/^__TARFILE_FOLLOWS__/ {{ print NR + 1; exit 0; }}' $0`
THIS=`pwd`/$0
ORIG_FOLDER=`pwd`
TEMP=`mktemp -d ./temp_installing_DesignExplorer_XXXXXX`
if ( tail -n +$SKIP $THIS | tar xzf - -C $TEMP ); then
    cd $TEMP
    # debug mode for installation if any arguments supplied
    if [ $# -ne 0 ]; then
        echo blargl > debug_installation
    fi
    ./install.sh $*
fi
# remove the temp folder only if it succeeded
# and print some helpful messages
#if [ ${PIPESTATUS[0]} -eq 0 ]; then
if [ $? -eq 0 ]; then
    cd $ORIG_FOLDER
    # delete installation files only if no arguments (not debug mode)
    if [ $# -eq 0 ]; then
        rm -rf $TEMP
    else
        echo "Installation Debug Mode, see $TEMP for the installation files"
        echo "after editing the install files, just run install.sh"
        echo "to try again.  Make sure the current directory is $TEMP when"
        echo "running install.sh"
    fi
    echo
    echo "DesignExplorer was successfully installed.  Please find a file named DesignExplorer"
    echo "in your home directory to start the program."
    exit 0
else
    echo
    echo "There were problems installing DesignExplorer"
    echo "Please contact someone for help, providing all the console output that was shown"
    echo "You may also be asked to send $TEMP , so don't delete it yet"
fi
exit 1
__TARFILE_FOLLOWS__
'''
    
with open(opath,'w') as f:
    f.write(extractor)
    
payload = opath+'_payload.tar'

def add(folder,stuff,first=False):
    if first:
        cmd = 'tar cf {} --directory={} {}'.format(payload,folder,stuff)
    else:
        cmd = 'tar --append --file={} --directory={} {}'.format(payload,folder,stuff)
    
    print(cmd)
    res = envoy.run(cmd,cwd=folder)
    print(res.std_out)
    print(res.std_err)

add(jkpy_parent,'jkpy/*.py jkpy/*/*.py jkpy/*/*/*.py jkpy/envoy/LICENSE',True)
add(de_parent,'DesignExplorer/*.py licenses')
add(de_parent+'/installer', 'install.sh install.py internal_launcher.sh internal_launcher.py external_launcher.sh')
add(de_parent, 'images/*.png')
add(de_parent, 'docs/manual/*.pdf docs/workbook/*.pdf')


res = envoy.run('gzip -c {} >> {}'.format(payload,opath))
print(res.std_out)
print(res.std_err)
os.chmod(opath,int('777',8))
os.remove(payload)

#fixme: a robust launcher for the user
'''
Nautilus at some point saw fit to disallow the execution of exectable "text" files by default.  So like everything is broken.

maybe make a binary somehow?  http://stackoverflow.com/questions/6423007/how-to-compile-a-linux-shell-script-to-be-a-standalone-executable-binary-i-e

for now, at least have the user's launcher state clearly in comments at the top IF YOU ARE READING THIS etc...?


something like this could do it, for nautilus at least...
    gsettings set org.gnome.nautilus.preferences executable-text-activation true
    or gconf-editor or gconftool-2 or dconf-editor or dconf bleh stop changing names!@#O!@KPOJ
    and I don't have all these systems to test it on. 
    seems like I have gsettings, no gnome though.

It is worse for the installer though.  Users have to chmod+x that thing.  Unless I spend even more time
figuring out how to package things into rpms and debs and all that mess, targeting all platforms specifically...
'''

# idea for a warning, but... 
#
#                 !!!! READ THIS !!!!
#
#
# IF YOU ARE READING THIS AFTER DOUBLE CLICKING THE FILE
# AND YOU EXPECTED TO START DesignExplorer, THEN YOUR FILE
# BROWSER PROGRAM IS PROBABLY BEING DUMB.  IS IT NAUTILUS?
# IF SO, GO TO THE EDIT MENU -> PREFERENCES -> BEHAVIOR
# AND UNDER THE "EXECUTABLE TEXT FILES" CHOOSE THE OPTION
# THAT SAYS "RUN".  (or use something better than Nautilus!)
#
# Backup plan is to run this file from the terminal.  For example,
# if the file is named DesignExplorer, you can open a terminal in that
# same directory and run the following command:
#        ./DesignExplorer &
#