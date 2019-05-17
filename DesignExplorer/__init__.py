from __future__ import absolute_import

#clean: for release, would not be exposing everything like this.
# but for development it is very useful
from .common import *
from .Main import *

'''
Main is the main application here.  It controls the file menu, design tabs,
gives permission to use the disk, etc.  Main has a dock area for Visualizations.
Main can operate under different Modes.  

Design wraps the StimSim stuff.  It represents a single experimental design.
Anything that uses a Design can modify the design (with some noted limitations).
When a Design is changed, it will notify Main, which will then notify all
Visualizations and Modes.  see DesignWatcher for the interface of notifications.
This system of notifications allows Visualizations to be fully independent of eachother,
also independed of the Mode.

Visualizations are dockable windows, used for any visualization of quality metrics
or graphs or whatever.

Modes establish what operations can be performed by the user.  They set the 
main interface Widget on Main (for example, the config table etc. in the DesignMode).
They typically have control over what Visualizations are available during the Mode
(in that they are what give the user the option to spawn the visualizations).
When a Mode is set, all previous Visualizations are closed.  Note that Modes have
to ask Main for things that don't involve the Mode provided Widget.  They can't add
Visualizations directly, but instead request it (this way, Main can first check
if there is an existing Visualization that fits the bill).

I'm removing all support for typed configs.  For example, safe cue cannot have
a longer duration than threat cue.  Some special details can be typed (styles,
simulation noise and betas) but the core design details cannot depend on type.
StimSim doesn't have this limitation, but typically typed configs aren't used.
Given how much it would complicate the interface and coding, I say typed configs
won't be added any time soon if ever.
'''



'''
#fixme: save/load error reporting and recovery needs at least one more pass

I think it is OK to leave this slightly unfinished feature-wise.  report errors, don't
mess things up, but can hold off on implementing lots of recovery systems.  At least until
the basic stuff is better tested.
'''

#idea: only way to change which designs are selected is to use the list dialog
# is that OK?  would it be useful to hide unselected designs (I think not, but consider further)?

#impl: improve the project launcher

#idea: did I really want selection boxes 


#impl: user needs some way of choosing the project name in Main

#idea: might be nice to let them add a description of sorts as well

#fixme: ensure all save operations are atomic.  defeats the purpose of an auto-save
# system if it has the ability to corrupt the saved data.


#fixme: rewrite pplib to use qt?  or at least disable for Macs in the mean time.
# very surprised that the tk gui of pplib failed on Dustin's Mac, especially
# without clear/reasonable error messages and even crashing the Python console.
# For what possible reason could Tk be imported without error yet result
# in such a failure??
#fixme: wow, kernel died after (?) I had to force close the optimization gui.  I've not seen that
# happen on my machine for a very long time.  Maybe this isn't a Mac only issue?

#annoy: OptimizeGUI doesn't close when closing main from console.  The users
# probably won't do that, but I do it frequently...



#impl: need to do a lot more thinking about feedback given to user
'''
simply setting a status box message is insufficient... what if there are multiple errors from a single operation?
is it possible to identify the single operation?  Maybe instead need to show a message queue in which
messages don't go away until the problem is fixed or the user dismisses it?  Or make it like a terminal with
autoscrolling messages?

and if there are too many warnings, users will need some way to turn things off or hide them...
'''


#idea: use properties for the simulation data object so that deconvolve isn't called when it isn't needed
#fixme: simulation Visualizations are messed up, need to clean up and ensure they are triggered to update properly (including
# initial creation).
#idea: an optional auto-update mode for simulation, or perhaps it just happens by default if N is 1?

#impl: finish Simulate and Visualize Modes


#fixme: the design and config tables resize after drag/drop or adding a new row, it is very jarring.
#impl: need to make the table columns resize more intellegently.  remove/copy buttons
# can be a fixed minimal size.  name needs to be largest.  inter/pre/post/max_consec/N can be enough
# for 3 numbers each.  type next priority.  everything else lower priority.
'''
with ResizetoContents mode for the table, it looks like the buttons are behaving differently than
the text areas.  modifying the text areas you see autosizing.  buttons don't...
    if modifying a text area, then the buttons do get resized.  so maybe my PickerButtons aren't
    emitting the proper signals?
'''


#idea: for plots in which lnies might overlap, good to have more sensible z ordering and differing thicknesses.  also perhaps highlight on over for the
# legends?

#idea: merge model and regression mode.  remove IM regression mode.  now that merged, can
# have AM1 default for certain models (convenient!).  Will require special handling for the 
# table though.

#idea: I only did a quick implementation of reverting invalid reconfigs in VisualizeMode.
# The user interface problably needs improved there.

#idea: if 'run' is a required part, it should be there by default and user
# should not be allowed to delete or rename it.

#impl: system for launcing a focus-following visualization.  I have Visualizations
# that should work, but how does the user make it show up?

#idea: collapse the visualization area when not used

#impl: plenty of things to make prettier.  learn stylesheets?

#impl: tooltips everywhere! (Gizmos have a param for tooltips, which helps)

#fixme: if the user doesn't define a quality metric or does define one then
# invalidates it by changing the design, what happens and how should it be handled?
# if no metric set, quality is 'infinite'.  Haven't tested invalid metric yet.

#impl: PlayMode





#impl: new file browser dialog, didn't see one built in?
# need to figure out how well just QFileDialog works
# and if I can use that to restrict single selections.

#fixme: throughout need to be using better path handling (os.path.join, stop with the trailing slashes)



#impl: remove jkpy dependencies.  There are a good number of these, but
# it would be much nicer to have this project be fully separate from
# my personal Python library (even if I share it with others in the lab,
# I'm not at all ready to make it fully public).
# StimSim also has jkpy dependencies.


'''
#impl: import?  
    can import from an export easily (just save the Design with it)    
    importing from StimStim style code or a StimSim.Experiment isn't hard either,
    just have to set some sane defaults where there is missing information.
    
    can't fully import from stim files and 3dD script though, no constraint details...
    and would have to infer the hierarchy somehow and make placeholder names... I
    don't see this type of import ever being implemented.
'''







'''
#fixme: visualization raising still can be improved
trying to raise on initial creation doesn't work properly.  updateGeometry and QApp.instance.processEvents didn't help
so I'm thinking it is related to the buffer space I put in the scroll area?  

'''






###########################################################################################################
## lower priority



#idea: 'add missing' button for DesignMode, adds config rows based on the defined parts.
# similarly, 'remove unused'
#idea: is there anything wrong with having config rows added/removed/renamed as parts are edited?
# the issue seems so unimportant though, is it even worth considering?


#idea: need a more convenient system for handling axis limit rules/locks

#idea: option to auto select focused design?  when unfocusing it would return to previous
# selection state?  Main should probably have it listed first in selectedDesigns()
# or last, just to be consistent.

#idea: any way to shortcut to the design by clicking on parts of the Visualization?  maybe?

#impl: need to consider how new Visualizations are added to the dock area.  to the right?
# below?  tabbed?  configurable?  It gets messy when there is a complex nested dock arrangement.

#idea: my current table implementation does not support drops into the cells.
# it is a bug, but I don't think the feature is important enough to justify fixing
# it yet...
#annoy: disabled cells in my Table can't be focused...  unexpected.

#idea: this GUI doesn't support manual ordering of event types (StimSim does, with
# eventlists).  Is it an important enough feature for students to have this?  
# only Srikanth has really used the feature to ensure balancing in congruent vs
# incongruent tasks.

#clean: as usual, my coding conventions are inconsistent.  Even disregarding
# things like common.py which came from the earlier version, it would be nice
# to fix all the inconsistencies.  which methods/attributes should be underscored, for example?
# Helper classes should also be prefixed with an underscore, else there can be confusion
# over which classes to use.




'''
#fixme:
got this error trying the old explorer on Windows.  perhaps seaborn missing?
or an outdated something?  However...  I'd prefer this not to happen...


Traceback (most recent call last):
  File "C:\Workspace\Coding\PythonToolbox\jkpy\decorators\_decorators.py", line 681, in wrapper
    return fn(*args,**kwargs)
  File "DesignExplorer\MainGUI.py", line 212, in _clickDesign
    dia = DesignGUI(main)
  File "DesignExplorer\DesignGUI.py", line 603, in __init__
    fw = FigureWidget()
  File "DesignExplorer\common.py", line 1309, in __init__
    self.fig = Figure(*args,**kwargs)
  File "C:\Anaconda\lib\site-packages\matplotlib\figure.py", line 328, in __init__
    linewidth=linewidth)
  File "C:\Anaconda\lib\site-packages\matplotlib\patches.py", line 593, in __init__
    Patch.__init__(self, **kwargs)
  File "C:\Anaconda\lib\site-packages\matplotlib\patches.py", line 95, in __init__
    antialiased = mpl.rcParams['patch.antialiased']
KeyError: u'patch.antialiased'
'''




'''
consider rotating visualizations to use space better, specifically Simulate

beta error plot, strange N=1 bar xlim

simulate mode progress bar

have status box automatically close/open if empty/issue

dump hexbin, use ribbon as default.  
'''
