#! /bin/bash
# first stage launching script for DesignExplorer

cd ~/.DesignExplorer/bin
# don't want any external Python stuff getting in
unset PYTHONPATH
# apparently matplotlib saves stuff in a common location by default.
# not sure how that works with multiple versions installed.
# not OK to potentially change the user's matplotlib settings though,
# so tell it to use a different location.
export MPLCONFIGDIR=~/.DesignExplorer/bin/other

# I think this is required?  hopefully will not cause issues with 3dDeconvolve...
unset DYLD_LIBRARY_PATH
unset DYLD_FALLBACK_LIBRARY_PATH

miniconda2/bin/python internal_launcher.py