from __future__ import absolute_import
from .common import *


class DesignWatcher(object):
    '''
    A base class for Visualizations and Modes to use for design callbacks.
    Default implementation is pass.  designChanged is called for any change.
    
    **kwargs used for potential future changes
    
    keep in mind that design might be None in some circumstances
    '''
    def designRenamed(self,design,old_name=None,**kwargs):
        # design's name changed from old_name to design.name
        self.designChanged(design)
    def designRemoved(self, design,**kwargs):
        # this design will be deleted soon.  it is no longer listed
        # as a loaded design.  it will not be the focused design
        self.designChanged(design)
    def designAdded(self, design,**kwargs):
        # a new design!
        self.designChanged(design)
    def designOptimized(self,design,**kwargs):
        # the design has been reoptimized, so quality metric and orderings will be changed
        self.designChanged(design)
    def designSelected(self,design,**kwargs):
        # design added to the global selection
        self.designChanged(design)
    def designDeselected(self,design,**kwargs):
        # design removed from the global selection
        self.designChanged(design)
    def designReconfigured(self,design,**kwargs):
        # changes were made to the design configuration sucessfully.
        self.designChanged(design)
    def designInvalidated(self,design,**kwargs):
        # the design is no longer valid
        # note that if you accidentally invalidated the design (say with Design.restart)
        # you will get this message before getting the exceptions that explain what was wrong.
        self.designChanged(design)
    def designFocused(self,design,**kwargs):
        # this design is focused in the Main gui
        # design can be None if no design is focused (happens if no designs available)
        self.designChanged(design)
    def designExtraChanged(self,design,what=None,**kwargs):
        # some extra property of the design was changed, see setExtra and related design methods
        # 'what' containes the name of this property.
        self.designChanged(design)
    def designStyleChanged(self,design,**kwargs):
        # the plot style hints have been modified (perhaps event "X" now should
        # be colored red instead of blue).  It is good to keep a consistent visual
        # style throughout where possible.
        self.designChanged(design)
    def designChanged(self,design):
        # all notifications default use this, so if you are lazy
        # you can just redo the entire visualization for any change without
        # checking if it was really necessary
        pass
    
'''
class ModeManagedVisualization(BaseVisualization):
    #opt: could maybe disable all the design messages?
    # or would a pure virtual IDesignWatcher or something
    # be better?  probably doesn't matter, so doing nothing.
    pass
'''

class BaseMode(DesignWatcher):
    '''
    class attribute title is the mode tab title
    
    must be added to Main's list of available Mode types (see Main.available_modes)
    
    you do not own the widget (close here will close the widget)
    if you for whatever reason want to change the widget,
    close the old one yourself.
    '''
    title="unimplemented mode"
    def __init__(self,main):
        DesignWatcher.__init__(self)
        self.main = main
        self.widget = self.makeWidget()
        main.setModeWidget(self.widget)

    
    def makeWidget(self):
        # make a new widget every time this is called, will be set as the mode widget
        # in the Main GUI.
        return QWidget()
    
    def close(self):
        self.widget.close()
    
    def addedToMain(self):
        # only after __init__ is everything back to a valid state.  For example,
        # during __init__ Main has yet to set this Mode as the current mode.
        pass
    
class ExampleMode(BaseMode):
    title="Example Mode"
    def __init__(self,main):
        BaseMode.__init__(self,main)
    
    def makeWidget(self):
        return QLabel()
    
    def designFocused(self,design,**kwargs):
        if design is None:
            txt = 'No Design'
        else:
            txt = design.name
        self.widget.setText(txt)


class BaseVisualization(DesignWatcher):
    '''    
    Dockable visualization
    
    '''
    def __init__(self, main):
        DesignWatcher.__init__(self)
        self.main = main
        
        #fixme: not sure if this is a good feature or not.  if used,
        # interface may change
        if main:
            self.options = main.getDefaultOptions(type(self).__name__)
        else: # just a test mode
            self.option = {}
        
        name = self._getDefaultName()
        self.widget = DockWidget(name)
        connect(self.widget.closed,self.close)
    
    def onModeMessage(self,msg,**kwargs):
        '''
        Modes will sometimes broadcast messages to all Visualizations.  But unless
        you are waiting for a message, don't bother implementing this.
        '''
        pass
    
    @property
    def name(self):
        # this is also the window title
        return self.widget.title()
    @name.setter
    def name(self,v):
        self.widget.setTitle(name)
    
    def getMode(self):
        return self.main.getMode()
    
    def _getDefaultName(self):
        '''
        derived types should implement this to figure out what to name itself (window title as well).
        Most will likely have a constant name.  A few will need to look at self.main to decide.
        '''
        return 'Invalid Plot Name'
    
    def close(self,*args,**kwargs):
        self.main.onVisualizationClose(self)
        self.widget.close()
    
    def saveDefaultOptions(self):
        '''
        use this to save a dictionary of configuration settings, such that they will
        be used for future instantiations (given as the 'options' parameter)
        
        feature might be removed, not sure if it is a good feature yet.
        '''
        self.main.saveDefaultOptions(self.__name__,self.options)
    
    def matchesActiveState(self,**kwargs):
        '''
        called by Main to determine if this instance should be used when the user
        is asking for this type of visualization.  Most visualizations will
        always return True (the default).  But if multiple instances of this
        type may exist, you'll have to reimplement.  for example if you have a single
        design focused visualization, you could check if your design is the currently
        active design in self.main.
        
        kwargs are as would go to __init__ (excluding main)
        '''
        return True
    
    @property
    def docked(self):
        # true is visualization window is docked (tabbed or not)
        return not self.widget.isFloating()
    @property
    def floating(self):
        # false if window is actually docked
        return self.widget.isFloating()
    @property
    def tabbed(self):
        # true if window is part of a tabbed group of Visualizations
        if self.floating:
            return False
        return self.main.dock.tabifiedDockWidgets(self.widget)
    
    def focus(self):
        # focus the visualization and make sure the user is able to see it.
        # will scroll as needed, change active tabs, make top level window, whatever
        # is required.
        if self.floating:
            self.widget.raise_()
            self.widget.activateWindow()
        else:
            if self.tabbed:
                self.widget.raise_()
            else:
                #self.widget.updateGeometry()
                #QApplication.instance().processEvents()
                bb=self.widget.geometry()
                x=bb.x()
                y=bb.y()
                w=bb.width()
                h=bb.height()
                sa=self.main.dock_scroll
                m=1
                #sa.ensureVisible(x+w,y+h,m,m)
                #sa.ensureVisible(x,y,m,m)
                sa.horizontalScrollBar().setValue(x)
                sa.verticalScrollBar().setValue(y)
                #self.main.dock_scroll.ensureWidgetVisible(self.widget)
                self.widget.setFocus()

class TestVisualization(BaseVisualization):
    next_id = 0
    def __init__(self, main, name=None):
        BaseVisualization.__init__(self, main, name)
        self.label = l = QLabel()
        l.setAlignment(Qt.AlignCenter)
        
        self.widget.setWidget(l)
        self.state = 'X'
        
        self.update()
    
    def _getDefaultName(self):
        if self.main:
            return str(len(self.main.visualizations))
        else:
            name = str(TestVisualization.next_id)
            # strange, didn't know that you can't use 'self' here!
            TestVisualization.next_id+=1
            return name
    
    def update(self, **unused):
        if self.state=='X':
            self.state='O'
        else:
            self.state='X'
        
        self.label.setText(self.name + ' ' + self.state)
    
    def matchesActiveState(self):
        # this test type will always add new instances
        return False


class SingleDesignVisualization(BaseVisualization):
    '''
    A convenient base class for Visualizations that only care about a single design.
    This design can be "only_focused", which means the design will change to match the
    focused design at all times.  Otherwise, the design will be whatever is currently
    focused at the time of creation and then never changed afterwards.
    '''
    def __init__(self,main,only_focused = False):
        self._watched_design = main.focusedDesign()
        self._only_focused = only_focused
        BaseVisualization.__init__(self,main)
    
    def update(self,design):
        pass
    def clear(self):
        pass
    def refresh(self):
        self._update(self._watched_design)
    
    def _makeName(self):
        if self._only_focused:
            return self.title
        if not self._watched_design:
            return 'close me'
        return self._watched_design.name + ' ' + self.title
    def _getDefaultName(self):
        return self._makeName()
    
    def _update(self,design):        
        if not design or not design.valid():
            self.clear()
        else:
            self.update(design)
    def designFocused(self,design,**kwargs):
        if self._only_focused:
            self._watched_design = design
            self._update(design)
    def designChanged(self,design,**kwargs):
        if design == self._watched_design:
            self._update(design)
    def designRenamed(self,design,**kwargs):
        if self._watched_design == design:
            self.name = self._makeName()
    def designSelected(self,design,**kwargs):
        pass
    def designDeselected(self,design,**kwargs):
        pass
    def designAdded(self,design,**kwargs):
        pass
    
    def matchesActiveState(self,only_focused=False,**kwargs):
        if self._only_focused:
            return only_focused
        return self._watched_design == self.main.focusedDesign()

class SingleDesignFigureVisualization(SingleDesignVisualization):
    '''
    A convenient base class for Visualizations that follow a single Design
    and also use a matplotlib figure.  
    '''
    def __init__(self,main,only_focused=False):
        SingleDesignVisualization.__init__(self,main,only_focused=only_focused)
        self.fw = FigureWidget()
        self.f = self.fw.fig
        self.ax = self.f.add_subplot(1,1,1)
        self.widget.setWidget(self.fw)
    def clear(self):
        # clear the axes
        self.ax.clear()
    def allowPanning(self):
        # call this once to enable panning on the figure.  I don't honestly know
        # if this can be toggled on/off, but probably doesn't matter.
        tb = NavigationToolbar(self.f.canvas,None)
        tb.pan()
        self._pan_toolbar = tb
    def _update(self,design):
        super(SingleDesignFigureVisualization,self)._update(design)
        self.fw.redraw()
    
class Design(object):
    '''
    Only to be created by Main.
    
    Holds all the details regarding an experimental design as it pertains to DesignExplorer.
    
    You must check if the Design is valid() before attempting to use most features.  For
    example, you'll get an Exception if you ask for the design matrix if not valid().
    
    Feel free to change values via the appropriate setters, notifications will be sent
    out automatically.  But do not do silly things like design.eventNames()[0][3] = "new name"...
    
    Design will not keep track of invalid designs.  If you try to configure it with invalid design settings, you will
    not be able to recover what you put in (like design names or event configurations).  keep track of all that yourself
    at least until the design is valid.
    '''
    
    STATE_NAMES = ('EMPTY','UNOPTIMIZED','OPTIMIZED','TWEAKED')
    @property
    def state(self):
        '''
        Design.EMPTY:
            There is no design yet, just some basic info like name
            or if the tab is focused in Main.  use reconfig to get started.
            Might actually be other details still present, but you shouldn't rely
            on them or use them.  They are only there such that when reconfig() is done
            sucessfully previous settings won't have been lost.  Similarly, don't assume
            that previous settings won't be lost...  it is a goal, but far from fully realized.
        Design.UNOPTIMIZED:
            You should optimize it before trusing any of the quality metrics.  You can still
            access all those values, but probably trash.  Visualizations probably should not care
            about this, it is instead a warning to the user that they really should optimize the design.
        Design.OPTIMIZED:
            Assuming it was thoroughly optimized (sufficient number of iterations, well thought out optimization metric, etc.),
            the quality metrics can now be trusted.  see also optimizationSettings, will let you know exactly
            what parameters were used for optimizing the design.  Again, there is no helpful cutoffs here...
            perhaps the user only did 10 iterations (in which case the Design almost assuredly isn't properly optimized
            despite the state saying "OPTIMIZED").  But that's the user's fault.
        Design.TWEAKED:
            The design was once optimized, but has had minor changes since (such that the previous optimization *probably* still applies to this design)
            Currently, you won't see this state much at all.  Identifying "minor" changes is largely unimplemented.
        
        It is generally your responsibility to ensure .valid() before accessing quality metrics and such.        
        '''
        return self._state
    
    def __init__(self, main, folder=None, name=None, exp=None, optimization_settings=None):
        '''
        init modes:
            load existing = only folder specified
                reads saved Design from the given folder
                can fail
                does not automatically focus in Main
            load from Stimsim.UserExperiment = only exp specified, optionally optimization_settings
                can fail
                does not automatically focus in Main
            new design = name and folder provided
                blank (invalid) Design created in given folder
                should not fail
                focused in Main (since it is invalid and needs to be edited)
        
        And this should only be instantiated through Main.  It isn't safe to create a Design externally
        and then load it into Main, may miss important validation steps that way.
        '''
        self._main = main
        self._folder = folder
        self._name = name
        self._temp_folder = main.requestTempFolder()
        if not self._temp_folder:
            raise RuntimeError('why is the folder blank!?')
        
        #clean: why was _selected not set on self._load?  seems odd, is it set in Main?
        
        # load from a StimSim.Experiment
        if exp:
            if not folder:
                raise RuntimeError('folder was not specified')
            self._fullClear()
            self._importExperiment(exp,optimization_settings)
            self._selected = False
        # load from the folder, find the name there
        elif folder and not name:
            self._load()
            self._selected = True
        # default values for a new design
        else:
            if not name:
                raise RuntimeError('name was not specified')
            if not folder:
                raise RuntimeError('folder was not specified')
            self._fullClear()
            self._selected = True
            
            
            
    def _fullClear(self):
        '''
        _clear, but clears a few more things
        '''
        self._clear()
        # these don't need to be in _clear.  they could go there, but
        # it is kinda convenient to have global noise for example persist
        # as a default?  maybe?
        self._global_noise = (0,0)
        self._orderings = dict()
        self._optimization_settings = dict()
        
    
    def __str__(self):
        return '<{} Design "{}">'.format(Design.STATE_NAMES[self.state].capitalize(),self.name)
    __repr__ = __str__
    
    def export(self, folder=None, interactive=False, force_overwrite=False):
        '''
        
        exports timings and scripts etc into a selected folder
        
        Returns True if export succeeds, False otherwise.  The export might
        fail if the user doesn't select a folder or aborts due to potential
        overwriting...
        
        Parameters
        -----------------
        
            folder=None
                The folder into which the exported files will be copied.  If not
                specified and if interactive=True then a folder dialog will be
                displayed.
            
            interactive=False
                If True, GUIs may be shown at various stages (overwrite confirmation,
                folder selection dialog, etc).
            
            force_overwrite=False
                If True, automatically overwrite any existing files.
        
        '''
        if not folder:
            if not interactive:
                return False
            #idea: remember previous export location?
            folder = QFileDialog.getExistingDirectory(None,'({}) Choose Export Folder'.format(self.name))
            if not folder:
                return False
        
        # generate the important files as provided by the optimizer
        self._exp.generate()
        
        noid = self._exp.ID
        N = len(noid)
        
        pat = '{}/{}.*'.format(self._temp_folder,noid)
        #print(pat)
        src_files = list(glob(pat))
        #impl: create optimization script example?  have related code somewhere, can move into StimSim and Design
        
        overwrite_needed = False
        dst_files = []
        for spath in src_files:
            name = os.path.basename(spath)
            #if not name.startswith(noid+'.'):
            #    raise RuntimeError('unexpected file found in temp export folder: '+spath)
            name = self.name+name[N:]
            dpath = os.path.join(folder,name)
            dst_files.append(dpath)
            if os.path.exists(dpath):
                overwrite_needed = True
        print(overwrite_needed,force_overwrite,interactive)
        if overwrite_needed and not force_overwrite:
            if interactive:
                res = QMessageBox.question(self._main.window,"({}) Overwrite Existing?".format(self.name), 'some files will be overwritten if you continue', QMessageBox.Yes | QMessageBox.Abort, QMessageBox.Abort)
                if res==QMessageBox.Abort:
                    return False
            else:
                return False
        
        for src,dst in zip(src_files,dst_files):
            shutil.copy(src,dst)
        
        #impl: overwrite warning, using above system.
        self._exportEventTable(os.path.join(folder,self.name+'_event_table.csv'))
        
        return True
    
    def _exportEventTable(self,fpath):
        d = self
        
        onsets = d.onsets()
        durations = d.durations()
        rows=[]
        names2 = d.eventNames()
        for run in range(len(onsets[names2[0][0]])):
            for name in names2[0]:
                for (o,d) in zip(onsets[name][run],durations[name][run]):
                    rows.append([run+1,name,o,d,1])
            for name in names2[1]:
                for (o,d) in zip(onsets[name][run],durations[name][run]):
                    rows.append([run+1,name,o,d,0])
        
        #fixme: I don't think the len(name) sort works.  need to find a different way
        # if the sort is to be useful visually.
        
        # sort by event name length (hierarchy)
        rows = list(sorted(rows,key=lambda row: len(row[1])))
        # then onset
        rows = list(sorted(rows,key=lambda row: row[2]))
        # then run
        rows = list(sorted(rows,key=lambda row: row[0]))
        
        
        with open(fpath,'w') as f:
            f.write('index,run,name,onset,duration,is_modeled\n')
            for i,row in enumerate(rows):
                f.write(str(i)+','+','.join(map(str,row))+'\n')    
    def copy(self,name):
        # add a new design with the given name to Main
        return self._main.addDesign(name,self)
    
    @property
    def name(self):
        # Within a single project (as managed by Main) all Design names must be unique.  This is strictly enforced,
        # don't blindly try to rename a Design without being prepared for Exceptions.
        return self._name
    @name.setter
    def name(self,name):
        if name != self._name:
            old = self._name
            self._name = name
            self._main.designRenamed(self,old)
    
    @property
    def selected(self):
        # true if the design is currently selected.  This is different from being focused, instead
        # reflects which designs are to be visualized currently.  For example, a plot of VIF values
        # should only show the VIF values for designs that are selected.
        return self._selected
    @selected.setter
    def selected(self,selected):
        if self._selected != selected:
            self._selected = selected
            if selected:
                self._main.designSelected(self)
            else:
                self._main.designDeselected(self)
    
    @property
    def focus(self):
        # only one Design can be focused in Main at any given time.  This is the
        # focused Design tabbar tab.
        return self._main.focusedDesign() == self
    @focus.setter
    def focus(self):
        self._main.focusDesign(self)
    
    def remove(self,_notify=True):
        # delete temp folder and saved data, then notify
        # only Main should use the _notify parameter
        # warning:  something feels wrong about this removal system, changes
        # may happen soon.
        self._main.returnTempFolder(self._temp_folder)
        shutil.rmtree(self._folder,True)
        if _notify:
            self._main.designRemoved(self)
    
    #style: should this be a property with invalidate?  so many usages already in place
    # that I'd rather not make that change...
    def valid(self):
        # true only if there is an error free design specified (see reconfig).  Until
        # a valid design is established, most other values and features of Design will
        # be unavailable (or rather, they'll raise exceptions if you attempt to access them).
        return self.state != Design.EMPTY
    
    
    ##########################################################################################################
    ## various quality metrics, details about a (hopefully well optimized) design
    # you must check if .valid() first, else you'll get exceptions just trying
    # to access these values.
    
    def quality(self):
        # the quality value with regards to the optimization metric specified in .optimize()
        # lower is better.  If you've not yet specified a metric, then the quality will be inf.
        self._exp.evaluate() #annoying:  I didn't gate quality in StimSim for some reason??
        return self._exp.quality  
    def colinearity(self):
        # a pandas.DataFrame of colinearity between regressors.
        return self._exp.colinearity_table
    def qualities(self):
        # see quality.  This is instead a table of normalized standard deviation values per regressor
        # (these values are used to evaluate the quality metric used in optimization).
        # lets you know how well you can estimate specific regressors given the current design.
        # lower is better.
        return self._exp.nsd
    
    def eventNames(self, baseline=False):
        '''
        return (modeled_event_names,unmodeled_event_names)
        
        both will be sorted tuples
        
        many other methods for Design implicitly assume this is the ordering.
        For example, onsets() will be in this order without actually returning
        the event names.  eventNames()[0]+eventNames()[1] is the order. [WRONG, onsets is a defaultdict so no order...]
        
        use baseline=True if you need baseline events too
        '''
        if baseline:
            return (self._names[2],self._names[1])
        else:
            return (self._names[0],self._names[1])
    
    def onsets(self):
        '''
        return a mapping of event names -> 2D array of onsets (in seconds).
        first dimension is for each run.  Each run starts at time zero.
        '''
        return self._exp._all_onsets
    
    def durations(self):
        '''
        return a mapping of event names -> 2D array of durations (in seconds)
        first dimension is for each run.
        '''
        return self._exp._all_durations
    
    def x1D(self):
        '''
        returns a pandas.DataFrame representation of the design matrix.
        
        structured to match AFNI's x1D files.  the 'column' column will 
        contain the actual design matrix values over time for a given regressor.
        GLTs and such are not included.
        
        the BasisName column indicates which event each row of the dataframe corresponds to.
        
        the Label column is similar to BasisName but accounts for the possibility of multiple
        regressors per event (CSPLIN for example).  This is done by adding a suffix like "#0"
        or "#1" and so on.  Even events without multiple regressors will have this suffix in the
        Label column.
        
        note that you cannot assume the order of this dataframe.  You must consider the Label and/or
        BasisName columns to interpret it.
        
        see jkpy.afni.loadX1D() for more details
        '''
        return self._exp.x1D
    def vif(self):
        '''
        pandas.DataFrame of variance inflation factor
        '''
        #return self._exp.vif
        return self._exp.vif[self._reordering(polort=True)]
    def nt(self):
        '''
        the number of timepoints in the experiment
        '''
        return self._exp.nt
    
    def tr(self):
        '''
        the length of TR for the experiment
        '''
        return self._exp.tr
    
    def config(self):
        '''
        a Config instance from this design, see StimSim.  this is the raw config, can
        be useful for loading the current configuration to allow the user to modify it (via reconfig)
        '''
        # StimSim saves the provided Config as raw_config.
        # and I expect future versions to do something similar (to allow for better
        # partial reconfiguring).
        return self._exp.parts.raw_config
    
    def parts(self):
        '''
        a Parts instance from this design.  Similar to config(), this is a very
        implementation specific object that lets you load the previous state and
        then let users modify it (via reconfig).
        
        Only used by DesignMode currently, only DesignMode has a need to fully
        redesign a Design by changing the event names and such.
        '''
        return self._exp.parts
    
    def optimizationSettings(self):
        '''
        returns the most recent optimization settings, even if they no longer apply
        '''
        return self._optimization_settings
    
    ########################################################################################################
    ## some extra stored values, some modifiable, not stored in the InternalExperiment
    # these are more loosely managed.  Mainly a convenience, things like the order
    # of rows in the DesignMode or plotting styles.  A goal is to have as many of these
    # properties kept/updated for reconfigs (keep the style even after a rename) but
    # the current level of support is minimal.
    
    def _setStyles(self,**style_sequences):
        if self.state == Design.EMPTY:
            raise Exception('cannot set styles for an empty design')
        
        changed = False
        for kind,seq in style_sequences.items():
            old = self._styles.get(kind)
            if not old:
                raise ValueError('unrecognized style setting "{}"'.format(kind))
            if seq:
                if len(seq) != len(old):
                    raise ValueError('Incorrect number of "{}" given'.format(kind))
                if kind=='linestyles':
                    self._styles[kind] = tuple(expand_linestyle(s) for s in seq)
                else:
                    self._styles[kind] = tuple(seq)
                
                changed = True
        return changed
    def setStyles(self,**style_sequences):
        '''
        set all the matplotlib plot styles for events in this design.
        This includes both modeled and unmodeled events.  Not essential to the actual
        design, but can be good for users to have a consistent style scheme for all Visualizations.
        All Visualizations should endevour to use .style() when plotting.
        
        valid style types:
            linestyles
                may be abbreviated
                use '-' as a default or something
            colors
                may be abbreviated
            markers
                may be abbreviated.  will not work for bar plots (patches don't have datapoints)
                please explicitly use 'None' as a default.
        
        
        will emit a designStyleChanged message
        '''
        if self._setStyles(**style_sequences):
            self._main.designStyleChanged(self)
    
    def style(self,name_or_index,bar=False):
        '''
        returns a dictionary of valid styles for use with matplotlib.  linestyle
        values will be unabbreviated.  You may modify the dictionary, it is your copy.
        
        all values will be present.
        
        bar=True will omit 'marker' from the dictionary (as the marker style is
        not a valid style choice for bar plots in matplotlib)
        '''
        i = name_or_index
        if not isinstance(i,int):
            (A,B) = self.eventNames()
            try:
                i = A.index(i)
            except ValueError:
                try:
                    i = len(A)+B.index(i)
                except ValueError:
                    raise ValueError("{} is not a valid event name".format(i))
        
        ret = dict(linestyle=self._styles['linestyles'][i], color=self._styles['colors'][i])
        if not bar:
            ret['marker'] = self._styles['markers'][i]
        return ret
    def styles(self,modeled=True,bar=False):
        # returns a list of dictionaries for either modeled or unmodeled events, convenience around just style()
        (names,other)=self.eventNames()
        N0 = len(names)
        if modeled:
            return [self.style(i,bar=bar) for i in range(N0)]
        return [self.style(i+N0) for i in range(len(other))]
    
    def extra(self,what,i=None):
        '''
        getter for some extra detail attached to this design concerning only modeled events.
        Currently only "beta" and "noise" are available.
        
        style could potentially be included here, but current usage it is just more convenient
        to set all the styles at once.  
        '''
        arr = getattr(self,'_'+what)
        if i is None:
            return arr
        else:
            if not isinstance(i,int):
                names = self.eventNames()[0]
                try:
                    i = names.index(i)
                except ValueError:
                    raise ValueError("{} isn't a modeled event".format(i))
            return arr[i]
                
    def setExtra(self,what,*args):      
        '''
        setter, see extra method.
        
        setExtra('noise',event_index,event_noise)
        setExtra('noise',noises_for_all_modeled_events)
        '''
        if len(args)==1:
            setattr(self,'_'+what,args[0])
            self._main.designExtraChanged(self,what=what,i=None)
        else:
            arr = getattr(self,'_'+what)
            i = args[0]
            if not isinstance(i,int):
                names = self.eventNames()[0]
                try:
                    i = names.index(i)
                except ValueError:
                    raise ValueError("{} isn't a modeled event".format(i))
            
            arr[i] = args[1]
            self._main.designExtraChanged(self,what=what,i=i)
    
    
    def globalNoise(self):
        # noise that can be applied to all events (as apposed to varied noise levels per event type)
        # (mean,scale)
        return self._global_noise
    def setGlobalNoise(self,m,v):
        # noise that can be applied to all events (as apposed to varied noise levels per event type)
        self._global_noise = (m,v)
        self._main.designExtraChanged(self,what='noise',base=True)
    
    def noise(self,i=None):
        '''
        noise is an array of noise levels per modeled event in the order given
        by getNames.
        
        see extra
        '''
        return self.extra('noise',i=i)
    def setNoise(self,what,*args):
        #see noise and setExtra
        return self.setExtra('noise',*args)
    
    def beta(self,i=None):
        '''
        beta is an array of simulated beta values per modeled event in the order given
        by getNames.
        
        see extra
        '''
        return self.extra('beta',i=i)
    def setBeta(self,what,*args):
        #see beta and setExtra
        return self.setExtra('beta',*args)
    
    def userOrdering(self,kind,value=None):
        '''
        no notifications, only currently set by DesignMode
        for keeping track of the table orderings (perhaps the user cares what
        order they listed the parts/configs in).  Other Modes can read this
        value to maintain a consistent ordering for the user.
        '''
        if value is None:
            return self._orderings[kind]
        else:
            self._orderings[kind] = value
    
    ################################################################################################
    ## some tools
    
    def simulate(self,betas=None,N=None,beta_noise=None,noise=None,split=False):
        '''
        generate a simulated signal given all the input parameters.
        all noise is a normal distribution in which the standard deviation value is
        the 'noise level' you indicate.  noise=5 is a normal distribution with standard
        deviation of 5 (and mean of 0 always).
        
        parameters:
            betas=None
                defaults to betas of 1 for all events
            N=None
                returns a single signal, shape just NT.  if N is specified, return value
                for signals will be (N,NT) instead.  This lets you ask for multiple
                simulated signals at once (more efficient).
            beta_noise=None:
                if specified, the given betas will be randomly changed based on the individual
                noise levels provided.
            noise=None:
                if specified, the simulated signal will additionally be combined with 
                a random signal
            split=False:
                by default, only the simulated signal(s) "signal" is returned.  else, return is
                (signal, ideal, noisy_parts, ideal_parts, noisy_betas)
                
                ideal and ideal parts will not have length N (as there is no noise, this would be redundant)
            
        '''
        
        #for now, no support for simulating the baseline (though it is now deconvolved properly)
        
        '''
        x1D ordering is _exp.event_names_with_polort.  but input order in DesignExplorer is self._names[2]
        further, there isn't actually any polort input.
        
        current approach is to make an X matrix ordered the way I want and not including baseline params.
        '''
        
        if betas is None:
            betas = np.ones(len(self.eventNames()[0]))
        else:
            betas = np.array(betas)
        
        if N is None:
            single = True
            N = 1
        else:
            single = False
        
        if np.ndim(betas)!=1:
            raise NotImplementedError()
        
        nbetas = len(betas)
        
        xdf=self.x1D()
        
        # sort the design matrix by pulling from order the x1D dataframe
        X = np.array([xdf[xdf.BasisName==name].column.values[0] for name in self.eventNames()[0]])
        ideal_parts = (X.T*betas).T
        ideal = ideal_parts.sum(0)
        NT = len(ideal)
        
        if hasattr(beta_noise,'__len__'):
            if sum(beta_noise):
                beta_noise = np.asarray(beta_noise)
            else:
                beta_noise=0
        elif beta_noise:
            beta_noise=np.ones(nbetas)*beta_noise        
        if isinstance(beta_noise,np.ndarray):
            noisy_betas = np.tile(betas,(N,1))
            for i in range(nbetas):
                if beta_noise[i]>0:
                    noisy_betas[:,i] += np.random.normal(0,beta_noise[i],N)
            noisy_parts = np.empty((N,)+ideal_parts.shape,dtype=float)
            for i in range(nbetas):
                noisy_parts[:,i] = np.outer(noisy_betas[:,i],X[i])
            
            signal = noisy_parts.sum(1)
        else:
            '''
            if split:
                noisy_parts = np.tile(ideal_parts)
            else:
                noisy_parts = None
            '''
            #opt: can I not do these? or can I return views?  or is
            # it OK to return differening shapes depending on the inputs
            # ?  latter I think would break expectations.
            if split:
                noisy_betas = np.tile(betas,(N,1))
                noisy_parts = np.tile(ideal_parts,(N,1,1))
            signal = np.tile(ideal,(N,1))
        
        if noise is None:
            pass
        else:
            normal_noise=True
            try:
                (noise_mean,noise_scale) = noise
            except:
                try:
                    noise_mean=float(noise)
                    noise_scale=0
                except:
                    noise = noise(N*NT)
                    noise.shape=(N,NT)
                    normal_noise=False
             
            if normal_noise:
                if noise_scale<=0:
                    noise_scale=0
                if noise_mean<=0:
                    noise_mean=0
                
                if noise_scale:
                    noise = np.random.normal(noise_mean,noise_scale,(N,NT))
                else:
                    noise = noise_mean
             
             #idea: is it necessary to avoid negative signal?  why wouldn't deconvolution be ok with negatives?
            signal+=noise
        
        '''
                
                    
        
        
        if noise is None:
            pass
        elif noise:
            try:
                noise = float(noise)
            except:
                noise = noise(N*NT)
                noise.shape=(N,NT)
            else:
                if noise_mean is None:
                    noise_mean=0
                
                if noise>0:
                    noise = np.random.normal(0,noise,(N,NT))
                else:
                    noise = noise_mean
           
            signal+=noise
        '''
        if single:
            signal = signal[0]
            if split:
                noisy_parts=noisy_parts[0]
                noisy_betas=noisy_betas[0]
        
        if not split:
            return signal
        
        return (signal, ideal, noisy_parts, ideal_parts, noisy_betas)
    
    def _reordering(self,polort=False,reverse=False):
        '''
        temporary fix for badly ordered values from _exp
        '''
        if polort:
            good_order=self._names[2]
            names=self._exp.event_names_with_polort
        else:
            good_order=self._names[0]
            names=self._exp.event_names
         
        if reverse:
            (good_order,names) = (names,good_order)
        
        return [good_order.index(name) for name in names]
    
    def deconvolve(self, signals):
        '''
        given the signal(s), returns betas obtained via 3dDeconvolve
        using the current model.  if signals is 1 dimensional (length NT),
        return value will just be an array of betas shape len(eventNames()[0]).  Otherwise, return value
        will be 2 dimenisonal shape (len(signals),len(eventNames()[0]).
        '''
        #fixme: assumes that the stim files are created...
        # 
        #if self._exp._stim_paths:
        #    fpath = list(d._exp._stim_paths.values())[0]
        #    if not os.path.exists()
        
        self._exp._make_stimes(prefix=self._exp.prefix+'.')
        betas = self._exp.better_deconvolve(signals)
        
        return betas[...,self._reordering()]
        
    
    def plot_events(self,ax=None,styles=None):
        '''
        box plot thing for the events, not sure if this will be a method of Design in the future...
        '''
        if styles is None:
            styles=dict()
            for i,name in enumerate(self._names[0]+self._names[1]):
                styles[name] = self.style(i)
        #clean: should this even be implemented here?  why not a free function?
        self._exp.plot_events(ax=ax,styles=styles)
    
    ########################################################################################
    ## core state changers
    ##
    # see individual methods for details
    # note that a valid design can never become empty unless you explicitly invalidate it
    
    def _clear(self):
        self._exp = None
        self._names = self._beta = self._noise = self._styles = None
        self._state = Design.EMPTY
    
    def invalidate(self):
        '''
        call this to effectively clear the design.  valid() will be False.
        
        emits designInvalidated
        '''
        self._clear()
        self._main.designInvalidated(self)
    
    def reconfig(self, part_list=None, config=None, tr=None):
        '''
        changes the Design parameters.
            part_list is a list of Part objects
            config is a Config instance
            tr is a float
        
    
        
        if EMPTY
            (must provide part list, config, and tr!)
            if success
                UNOPTIMIZED
                designReconfigured
            else
                no change
                exception raised
        else
            if success
                if OPTIMIZED
                    OPTIMIZED if nothing actually changed, else TWEAKED if possible, else UNOPTIMIZED
                elif TWEAKED
                    TWEAKED if possible else UNOPTIMIZED
                elif UNOPTIMIZED
                    no change
                
                will attempt to keep old settings (styles, noise, betas)
                
                designReconfigured
            else
                invalid settings aren't remembered!
                
                if able to restore previous valid settings
                    no change
                    exception raised
                else
                    EMPTY
                    designInvalidated
                    exception raised (showing both original and restore attempt errors)
        
        
        eventually hope to rewrite StimSim such that it provides hints as to TWEAKED vs UNOPTIMIZED.
        but for now, such info is not available.
        '''
        if self.valid():
            self._reconfig(part_list,config,tr)
        else:
            self._restart(part_list,config,tr)
    
    def _restart(self,part_list,config,tr):
        '''
        build a new InternalExperiment from scratch.
        
        will be UNOPTIMIZED at end
        '''
        if None in (part_list,config,tr):
            raise Exception("Cannot reconfigure an empty design without providing part list, config, and tr")
        
        try:
            parts = Parts(part_list,config)
            ie = InternalExperiment('noid',parts,tr)
        except:
            raise
        
        self._exp = ie
        self._state = Design.UNOPTIMIZED
        
        # there can also be failures at this late stage,
        # so need to catch them and ensure the design
        # isn't incorrectly marked as valid
        try:
            self._refresh()
        except:
            self.invalidate()
            raise
        else:
            self._main.designReconfigured(self)
    
    def _refresh(self, regenerate=True):
        '''
        internal helper, see _reconfig and _restart (which are called from reconfig)
        
        Assume that exp has been changed, update all internal variables accordingly.
        
        no state change
        '''
        ie = self._exp
        ie.folder = self._temp_folder
        #annoy:  this is done only so that eventNames can be called
        # though it also calculates a few other things.
        # this is a problem with StimSim.InternalExperiment, I hope to
        # address it when I finally have time to rewrite StimSim.
        # bah, it was even buggy.  couldn't handle rests properly
        #ie._get_all_timings()
        #annoy: even worse, now have to generate in order to get the polort names
        # in the future there needs to be a StimSim method that generates the names
        # without doing anything else.  For now, I made generate at least not fail
        # for no modeled events so I can raise a better exception
        if regenerate:
            ie.generate()
        
        # messy approach to obtain event names in a consistent convenient format
        first = set(ie._event_names)
        if not first:
            raise Exception('must specify at least one modeled event')
        rest = set(ie._all_onsets)-first
        
        # like first, but with baseline params added to the very end
        # and since this is used for design matrix stuff all events currently have to have #0 even though
        # I hope to change that eventually and things like CSPLIN aren't supported yet anyways.
        first0 = set([name+'#0' for name in first])
        polort=set(ie.event_names_with_polort)-first0
        polort=sorted(first0)+sorted(polort)
        
        self._names = (names,more,polort) = (tuple(sorted(first)),tuple(sorted(rest)), tuple(polort))
        # reset the extra arrays
        N = len(names)
        self._noise = np.zeros(N)
        self._beta = np.ones(N)*50
        N+=len(more)
        self._user_styles = False
        #impl: have setStyles set user_styles to True.  need other resets?
        # if not user styles, feel free to do auto?  to avoid mixing auto
        # iteratively.
        self._styles = dict(linestyles=['solid']*N, colors=['black']*N,markers=['None']*N)
        
        '''
        nice = niceStyles(names)
        for kind in ('linestyle','color','marker'):
            arr = self._styles[kind+'s']
            for name,style in nice.items():
                try:
                    new = style['kind']
                except:
                    continue
                i = names.index(name)
                arr[i]=
        '''
        
    
    def _reconfig(self,part_list,config,tr):
        '''
        try to use the existing InternalExperiment for reconfiguring, also
        trying to keep any internal variables. 
        
        Tries to keep state high, but optimization may deteriorate depending on how big things change
        '''
        
        # previous settings to allow for recovery
        old_tr = self.tr()
        old_config = self.config()
        old_part_dict = self.parts().nodes
        # would like to keep these settings
        old_styles = self._styles
        old_noise = self._noise
        old_beta = self._beta
        # used to track changes
        old_names = self._names
        had_user_styles = self._user_styles
        #old_metric = self.metric()
        # currently not attempting to update the user metric as it is part of optimizationSettings
        
        # reconfig params
        kwargs=dict()
        if part_list is not None:
            kwargs['parts']=part_list
        if config is not None:
            kwargs['config'] = config
        if tr is not None:
            kwargs['tr'] = tr
        if not kwargs:
            return # nothing to do?
        
        try:
            # try to reconfigure
            self._exp.reconfig(**kwargs)
        except Exception as e:
            #bad = str_err(traceback=False)
            bad = str(e)
            # try to recover
            try:
                self._exp.reconfig(parts=list(old_part_dict.values()), config=old_config, tr=old_tr)
            except:
                # hopelessly broken
                worse = str_err()
                self.invalidate()
                raise Exception(reconfig_recovery_failed.format(bad,worse))
            
            
            # caller may try again
            #annoy: why do I have to specify the exception here?
            # it happens to work out for my current usage, but
            # I see no reason why the last exception should be 
            # None here.  if the recovery failed, it would raise
            # and exit before this point...
            raise e
        
        #success!
        self._refresh()
        
        # try to keep old values
        if part_list is None or self._names == old_names: 
            #perfect, can clearly keep all the old settings
            #well... cannot fully trust same names.  what if two names were swapped?
            # but for extra details like this it is fine to guess
            self._styles = old_styles
            self._noise = old_noise
            self._beta = old_beta
            #self._exp.metric = old_metric
        else:
            # at least restore values where the names match
            # (could get fancier and use rename details or try to match similar names)
            N = len(self._names[0])
            all_old_names = old_names[0]+old_names[1]
            for i,new_name in enumerate(self._names[0]+self._names[1]):
                try:
                    #opt: lookup hints, also lists are partially sorted...
                    oi = all_old_names.index(new_name)
                except ValueError:
                    pass
                else:
                    if i<N:
                        self._noise[i] = old_noise[oi]
                        self._beta[i] = old_beta[oi]
                    
                    for kind in ('linestyles','markers','colors'):
                        self._styles[kind][i] = old_styles[kind][oi]
        
        # consider state change (can we keep TWEAKED or even OPTIMIZED states?)
        if self.state != Design.UNOPTIMIZED:        
            #impl: major vs minor change detection
            
            def change_level():
                if part_list is not None:
                    '''
                    definitely can't change the number of types or parts...
                    too risky to treat that as a minor change.
                    
                    simple renaming shouldn't change optimization levels
                    But if names are swapped, then effectively the config
                    is changed.
                    
                    so for now, have to assume major change
                    '''
                    return 2
                if config is not None:
                    '''
                    there are ways that changes can be considered tweaks,
                    but I don't have time to implement this right now.
                    Ideally it would be implemented in my StimSim rewrite
                    (DesignEvaluator).
                    
                    There are some simpler tests that could be done here
                    in the mean time, but still a bit of work...
                    
                    so for now, assume major change
                    '''
                    return 2
                
                if tr is not None:
                    '''
                    Not actually sure how true this is...  to do it properly
                    would need to have the tr at which it was optimized.
                    then again, "minor change" is only ever going to be a guess.
                    '''
                    return 1
                '''
                could do even more change detection by forcing Design
                users to provide single change details.  In most situations,
                the changes made are minor (or can be made to be very minor).
                
                But that requires more work, and I want DesignEvaluator to
                do this in a different way eventually.
                '''
                
                return 0
            
            L = change_level()
            
            if L==1:
                self._state = Design.TWEAKED
            elif L==2:
                self._state = Design.UNOPTIMIZED
        
        # finally notify
        self._main.designReconfigured(self)
    
    def optimize(self,settings=None):
        '''
        provide a dictionary of optimization settings.  Otherwise a modal dialog
        will be shown through which the user will be able to optimize the design.
        
        The design will only be modified if the optimization is successfull.  If
        something goes wrong, an exception will be raised.
        
        see also optimizationSettings()
        '''
        if not self.valid():
            raise Exception("cannot optimize an invalid design")
        
        # gui mode, will call optimize again if appropriate (this time providing settings)
        if settings is None:
            from .Optimization import OptimizeGUI
            dia=OptimizeGUI(self)
            dia.exec_()
            return
        
        sim_folder=''
        try:
            sim_folder = mkdtemp()
            #fixme: MyPool GUI doesn't work on all systems (Mac screws up tkinter support for some reason).  need to get a working alternative progress feedback system in place.  but for now, just no GUI...
            ie = simulate_internal(self.parts(), folder = sim_folder, gui=False, **settings)._internal()
        finally:            
            if os.path.isdir(sim_folder):
                shutil.rmtree(sim_folder,True)
        
        # optimizing won't change things like event names, so those can be kept
        self._exp = ie
        self._optimization_settings = settings
        self._state = Design.OPTIMIZED
        self._refresh()
        self._main.designOptimized(self)
    
    ################################################################################################
    ## serialization
    '''
    Currently a very simple implementation.  header (lightweight), core (important and
    typically the most expensive to save), and other (extra details, typically not that large
    but also not critical to save).  All three saved to separate files in the save.  Just using
    pickle.  No actual version handling yet (hopefully never needed?).
    '''
    
    _serialization_version = 1
    
    def _read(self,name):
        with open(self._folder+'/'+name+'.pickle','rb') as f:
            return pickle.load(f)
    def _write(self, __write_save_file_name, **data):
        with open(self._folder+'/'+__write_save_file_name+'.pickle','wb') as f:
            pickle.dump(data,f,protocol=2)
    
    def __loadFrom(self,src):
        '''
        accesses the following keys of src:  header, core, other
        
        used for loading
        
        was originally basically _load.  the split isn't useful anymore/yet.
        '''
        h = src['header']
        version = h['version']
        if version != self._serialization_version:
            print('WARNING:  the save was created with a different version and might not work correctly')
            pass
    
        self._name = h['name']
        self._state = h['state']
        self._selected = h['selected']
        
        c = src['core']
        self._exp = c['exp']
        self._optimization_settings = c['opt']
        if self._exp:
            self._exp.set_dirty()
            self._refresh()
        
        o = src['other']
        self._global_noise = o['global_noise']
        self._orderings = o['orderings']
        self._styles = o['styles']
        self._names = o['names']
        self._beta = o['beta']
        self._noise = o['noise']
    
    
    @perr
    def _importExperiment(self,exp,optimization_settings):
        '''
        called when creating a new Design from a StimSim.UserExperiment (see __init__)
                
        state will either be OPTIMIZED or UNOPTIMIZED.
            EMPTY StimSim.Experiments don't exist
            TWEAKED is treated as UNOPTIMIZED
        '''
        if self._name:
            raise NotImplementedError('importing a StimSim experiment is meant for loading new Designs, not overwriting existing ones')
        
        # experiment should be mostly valid, else it wouldn't exist (StimSim should have checked most of it)
        
        self._exp = exp._internal()
        self._name = self._exp.ID
        
        if not optimization_settings:
            optimization_settings={}
        self._optimization_settings = optimization_settings        
        niter = optimization_settings.get('iterations',1)
        
        # choose the state
        if niter>1:
            self._state = Design.OPTIMIZED
        else:
            self._state = Design.UNOPTIMIZED
        
        # still need to do a last bit of validation and update our internal values
        #clean: StimSim should probably provide access to the state
        # might raise, that's fine
        if self._exp._has_generated:
            self._refresh(regenerate=False)
        else:
            raise Exception('why was this design not generated already?')
            self._refresh(regenerate=True)
            self._state = Design.UNOPTIMIZED
        
    @perr
    def _exportExperiment(self,name):
        '''
        returns a (StimSim.UserExperiment,optimizationSettings()).  User may modify
        them as desired (perhaps optimize them) and reimport later.
        '''
        import copy
        exp = StimSim.Experiment(copy.deepcopy(self._exp))
        opt = copy.deepcopy(self._optimization_settings)
        
        #figure out the state
        if self._state in (Design.UNOPTIMIZED,Design.OPTIMIZED):
            pass
        elif self._state == Design.EMPTY:
            raise RuntimeError('cannot export an empty design, that makes no sense')
        elif self._state == Design.TWEAKED:
            print('WARNING:  exporting a tweaked design, will be regarded as unoptimized if reimported')
            opt['iterations']=1
        else:
            raise RuntimeError('unrecognized design state, contact the developers')
        
        # have to modify ID and folder based on the internal object, UserExperiment
        # calls set_dirty for all attribute changes to be safe.  It doesn't seem
        # to matter for these attributes
        ie = exp._internal()
        ie.ID = name
        ie.folder=None
        #exp.ID = name
        #exp.folder=None
        return (exp,opt)
    
    @perr
    def _load(self):
        '''
        loads from self._folder, called by Main
        '''
        class Source(object):
            def __getitem__(me,name):
                return self._read(name)
        return self.__loadFrom(Source())
    
    def _saveHeader(self):
        self._write('header', version=self._serialization_version, name=self.name, state=self.state, selected=self.selected)
    def _saveCore(self):
        self._write('core', exp = self._exp, opt=self.optimizationSettings())
    def _saveOther(self):
        self._write('other', global_noise=self._global_noise, orderings = self._orderings, styles = self._styles, names = self._names, beta=self._beta, noise=self._noise)
    
    @perr
    def saveAs(self,folder,name):
        '''
        save the Design as if its folder and name were as given.  Used for copying designs.
        '''
        real_folder = self._folder
        real_name = self._name
        try:
            self._folder = folder
            self._name = name
            self.save()
        finally:
            self._folder = real_folder
            self._name = real_name
        
    @perr
    def save(self):
        #save everything
        self._saveHeader()
        self._saveCore()
        self._saveOther()
    @perr
    def saveHeader(self):
        # save just simple basic details like name and state
        self._saveHeader()
    @perr
    def saveCore(self):
        # save the expensive details (quality metrics, event ordering, etc)
        self._saveHeader()
        self._saveCore()
    @perr
    def saveOther(self):
        # save extra details that are convenient but not as important as the core.
        self._saveHeader()
        self._saveCore()
    
for i,name in enumerate(Design.STATE_NAMES):
    setattr(Design,name,i)

reconfig_recovery_failed='''Reconfig failed, and was unable to restore!  exceptions in order printed below.
Unfortunately, the design is lost.  Sorry, this shouldn't happen...
<reconfig error>
{}
<recovery error>
{}'''




#%%