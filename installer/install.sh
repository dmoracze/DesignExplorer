#! /bin/bash
# install script for DesignExplorer

# see build_installer.py for details of the file layout

TEMP_FOLDER=`pwd`

if [ -a debug_installation ]; then
    debug=1
else
    debug=0
fi

# figure out machine details
x=`uname -m`
if [[ "$x" == 'x86_64' ]]; then
    machine='x86_64'
else
    machine='x86'
fi
x=`uname`
if [[ "$x" == 'Linux' ]]; then
    platform='Linux'
else
    platform='MacOSX'
    
    if [[ "$machine" == 'x86' ]]; then
        echo "only 64bit for MacOSX supported" >&2
        exit 1
    fi
fi

# set up the folders
mkdir -p ~/.DesignExplorer
rm -rf ~/.DesignExplorer/bin
mkdir ~/.DesignExplorer/bin
cd ~/.DesignExplorer/bin

# download Python
url='https://repo.continuum.io/miniconda/Miniconda2-latest-'$platform-$machine.sh
echo $url
if hash wget 2>/dev/null; then
    wget $url -O mci.sh
elif hash curl 2>/dev/null; then
    curl -o mci.sh $url
else
    echo "neither curl nor wget seem to be available on your system, please ask for help"
    exit 1
fi
if [ $? -ne 0 ]; then
    echo "unable to download Miniconda" >&2
    exit 1
fi

##testing:
#echo testing a failure
#exit 1

# install Python locally
unset PYTHONPATH
unset DYLD_LIBRARY_PATH
# miniconda fails to unset this fallback path, can cause issues on Macs 
unset DYLD_FALLBACK_LIBRARY_PATH
chmod +x mci.sh
./mci.sh -b -p miniconda2
if [ $? -ne 0 ]; then
    echo "unable to install Python" >&2
    exit 1
fi

if [ "$debug" = 0 ]; then
    rm mci.sh
fi

# run the python part of the installer
miniconda2/bin/python $TEMP_FOLDER/install.py
if [ $? -ne 0 ]; then
    echo "installation failure, see above messages" >&2
    exit 1
fi

# get Python dependencies
# most are very small (some might be unnecessary, but none of the big ones are).
miniconda2/bin/conda install -y numpy scipy matplotlib seaborn pyqt=4.11.4 psutil pandas docutils sip six pillow h5py
if [ $? -ne 0 ]; then
    echo "unable to install Python dependencies" >&2
    exit 1
fi

# make anaconda clean up unused files
# fix: cleaning on Red Hat server
#miniconda2/bin/conda clean -a -y

# return to the temp folder and copy more stuff in
cd $TEMP_FOLDER
pwd
ls
PYLIB=~/.DesignExplorer/bin/miniconda2/lib/python2.7/site-packages
DEBIN=~/.DesignExplorer/bin
IMAGE=~/.DesignExplorer/bin/images
DOCS=~/.DesignExplorer/docs


if [ "$debug" = 0 ]; then
    op=mv
else
    op="cp -r"
fi

$op jkpy DesignExplorer $PYLIB
$op licenses internal_launcher.sh internal_launcher.py $DEBIN
$op docs $DOCS
$op images $IMAGE

LPATH=~/DesignExplorer
if [ -d "$LPATH" ]; then
    echo "why do you have a folder named DesignExplorer in your home directory?"
    echo "launcher will be named DesignExplorer.sh instead"
    LPATH=~/DesignExplorer.sh
fi

rm -f $LPATH
$op external_launcher.sh $LPATH
chmod +x $LPATH
