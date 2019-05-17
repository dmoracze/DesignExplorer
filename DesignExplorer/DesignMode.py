from __future__ import absolute_import
from .common import *
from .version import *

'''
All related to the initial design of experiments.  Limited visualizations, full ability to edit designs.
'''

class PartRow(Row):
    # a row of the "Parts" table
    #clean: shouldn't have to specify copy/remove...
    col_names=['remove','copy'] + 'name components types'.split()
    def __init__(self,owner):
        Row.__init__(self,owner)
        with self.build as add:
            add('name', tip='Name of event')
            add('components',get=Widget.as_strs, tip='Event components')
            add('types',get=Widget.as_strs, tip='Different event types (as in different conditions)')

class PartsTable(DesignTable):
    # a widget for manipulating the Parts of a Design.
    col_names = PartRow.col_names
    def __init__(self,owner, *args, **kwargs):
        DesignTable.__init__(self,owner,PartRow,*args,**kwargs)
    
    def parse(self):
        parts=self.data()
        
        names=set([])
        for part in parts:
            name=part['name']
            if name not in names:
                names.add(name)
            else:
                raise Exception('duplicates detected for part "{}"'.format(name))
        # process parts        
        part_list=[Part('experiment','run')]
        for p in parts:
            name=p['name']
            if name:
                part_list.append(Part(name,*p['components'],types=p['types']))
        
        return part_list
            
    def load(self, design):
        with signalsBlocked(self):
            self.clear()
            if design and design.state != Design.EMPTY:
                part_dict = design.parts().nodes
                
                names = self._sortedNames(design,'design_parts',list(part_dict))
                for name in names:
                    if name=='experiment':
                        continue
                    row = self.add()
                    part = part_dict[name]
                    row.set_data(dict(name=part.name, components = part.parts, types = part.types))
        self.tableDataChangedEvent()

class DesignModeVisualization(BaseVisualization):
    '''
    first Visualization made for the DesignMode.  just calls plot_events (poorly named!!)
    Will likely be improved and generalized.  plot_events surely won't last much longer, if
    only it gets renamed to plotEvents...
    '''
    def __init__(self, main):
        BaseVisualization.__init__(self,main)
        
        fw = FigureWidget()
        #fw.setSizePolicy(QSizePolicy.MinimumExpanding,QSizePolicy.MinimumExpanding)
        #fw.setSizePolicy(QSizePolicy.Minimum,QSizePolicy.Minimum)
        f = fw.fig
        ax = f.add_subplot(1,1,1)
        #fw.hide() #?
        
        tb = NavigationToolbar(f.canvas,None)
        tb.pan()
        
        
        self.tb = tb
        self.fw = fw
        self.f = f
        self.ax = ax
        self.locks = None
        
        self.widget.setWidget(self.fw)
        
        self.update()
    def _getDefaultName(self):
        return 'Event Plot'
    @perr
    def update(self):
        # handling is easy here, no other designs to consider for Design mode
        design = self.main.focusedDesign()
        self.ax.clear()
        self.locks = None        
        if design is None or not design.valid():
            return
        
        design.plot_events(ax = self.ax)
            
        # lock axes, have to save locks to avoid
        # garbage collection
        a = axisLimitLock(self.ax,'x',width=1)
        b = axisLimitLock(self.ax,'y')
        self.locks = (a,b)
        
        self.fw.redraw()    
    
    def designChanged(self,design):
        self.update()
    
#testing:
class DesignModeVisualization(BaseVisualization):
    '''
    first Visualization made for the DesignMode.  just calls plot_events (poorly named!!)
    Will likely be improved and generalized.  plot_events surely won't last much longer, if
    only it gets renamed to plotEvents...
    '''
    def __init__(self, main):
        BaseVisualization.__init__(self,main)
        
        self.fw = FigureWidget()
        ax = self.fw.fig.add_subplot(1,1,1)
        self.widget.setWidget(self.fw)
        self.cax = ConvenientAxes(ax,pan=True,limit=True)
        
        self.update()
    def _getDefaultName(self):
        return 'Event Plot'
    @perr
    def update(self):
        # handling is easy here, no other designs to consider for Design mode
        design = self.main.focusedDesign()
        self.cax.clear()
        if design is None or not design.valid():
            return
        
        with self.cax as ax:
            design.plot_events(ax=ax)
        
        self.fw.redraw()    
    
    def designChanged(self,design):
        self.update()

class DesignModeWidget(QWidget):
    '''
    When DesignMode is the active mode, this widget will be displayed in the
    Main GUI.  contains the Parts and Config tables, typically a user will fully create
    their experimental design using this widget before moving on to other modes for evaluating/tweaking the design.
    '''
    def __init__(self,mode):
        QWidget.__init__(self)
        self.mode = mode

        self.part_widget = PartsTable(self)

        editable = [col not in ('type','dist') for col in ConfigTable.col_names]
        self.config_widget = ConfigTable(self,  editable=editable)
        for name in ('type','dist'):
            i = ConfigTable.col_names.index(name)
            self.config_widget.setColumnHidden(i,True)
        
        layout = QVBoxLayout()
        bot = QHBoxLayout()
        buts = QHBoxLayout()
        bstyle = '''
            .QPushButton {
                background-color: #cccccc;
                font: normal 12px;
                border-style: outset;
                border-width: 1px;
                border-radius: 4px;
                border-color: black;
                width: 125px;
                height: 15px;
                padding: 4px;
                margin: 4px
            }
            .QPushButton:pressed {
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #999999, stop:1 #a6a6a6)
            }
        '''
        add_part_button = QPushButton()
        appendStyleSheet(add_part_button,bstyle)
        add_part_button.setToolTip('Insert row into the Event Definition Table')
        add_part_button.setText('Add Event')
        
        add_config_button = QPushButton()
        appendStyleSheet(add_config_button,bstyle)
        add_config_button.setToolTip('Insert row into the Event Configuration Table')
        add_config_button.setText('Add Configuration')
        
        load_button = QPushButton()
        appendStyleSheet(load_button,bstyle)
        load_button.setText('Load Example')
        load_button.setToolTip('Load example experiment')

        tip = 'Repetition time (in seconds)'
        tr_lab = QLabel('TR:')
        tr_lab.setToolTip(tip)
        appendStyleSheet(tr_lab,'''
            .QLabel {
                background: #ECECEC;
                font: normal 15px;
            }
        ''')
        self.tr_w = QLineEdit()
        self.tr_w.setAlignment(Qt.AlignCenter)
        self.tr_w.setText('2.5')
        self.tr_w.setToolTip(tip)
        appendStyleSheet(self.tr_w,'''
            .QLineEdit {
                background: #ffffff;
                border: 1px solid #000000;
                width: 60px;
                height: 20px;
            }
        ''')
        self.tr_w.setValidator(QDoubleValidator(0,100,2))

        self.revert_w = r = QPushButton()
        r.setText('Revert')
        appendStyleSheet(r,'''
            .QPushButton {
                background-color: #cccccc;
                font: normal 12px;
                border-style: outset;
                border-width: 1px;
                border-radius: 4px;
                border-color: black;
                width: 75px;
                height: 15px;
                padding: 4px;
                margin: 4px
            }
            .QPushButton:pressed {
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #999999, stop:1 #a6a6a6)
            }
        ''')
        r.setToolTip('Revert to previous state (if you need to)')
        r.setEnabled(False)

        help_button = QPushButton('?')
        help_button.setToolTip('Open user manual')
        appendStyleSheet(help_button,'''
            .QPushButton {
                    font-style: bold;
                    font-size: 10px;
                    color: white;
                    background-color: #0066ff;
                    border-style: outset;
                    border: 1px solid #000000;
                    padding: 2px;
                    height: 8px;
                    width: 20px;
                    margin: 4px;
                }
            .QPushButton:pressed {
                    background-color: #66ccff;
                }
        ''')

        tr_lay = QHBoxLayout()
        tr_lay.addWidget(tr_lab)
        tr_lay.addWidget(self.tr_w)
        tr_lay.setSpacing(10)

        hlay = QHBoxLayout()
        hlay.addWidget(r)
        hlay.addWidget(help_button)
        hlay.setSpacing(30)

        left_lay = QHBoxLayout()
        left_lay.addLayout(tr_lay)
        left_lay.addLayout(hlay)
        left_lay.setSpacing(30)

        buts.addWidget(add_part_button)
        buts.addWidget(add_config_button)
        buts.addWidget(load_button)
        buts.addStretch()
        buts.addLayout(left_lay)
        buts.setSpacing(30)
        
        s = QSplitter()
        s.setOrientation(Qt.Vertical)
        s.addWidget(self.part_widget)
        s.addWidget(self.config_widget)

        layout.addWidget(s)
        layout.addLayout(bot)
        bot.addLayout(buts)
        self.setLayout(layout)
        
        # connect at the end to avoid junk changed events
        connect(add_part_button.clicked, lambda *args: self.addRow('part'))
        connect(add_config_button.clicked,lambda *args: self.addRow('config'))
        connect(load_button.clicked,lambda arg: self.loadExample())
        connect(self.revert_w.clicked,lambda unused: self.mode.onRevertClicked())
        connect(help_button.clicked, lambda unused: self.hclick())
        connect(self.tr_w.textChanged, lambda unused: self.mode.onTrEdit())
        connect(self.config_widget.tableDataChanged, self.mode.onTableEdit)
        connect(self.part_widget.tableDataChanged,self.mode.onTableEdit)
        connect(self.part_widget.orderChanged, self.mode.saveOrdering)
        connect(self.config_widget.orderChanged, self.mode.saveOrdering)
        
    
    def load(self,design):
        # set a new design, like if the focused design is changed.  
        with signalsBlocked(self.part_widget,self.config_widget,self.tr_w):
            self.part_widget.load(design)
            self.config_widget.load(design)
            if design and design.valid():
                self.tr_w.setText(str(design.tr()))
            
        #testing:
        for w in (self.part_widget, self.config_widget):
            w.updateGeometry()
            w.resize(w.minimumSizeHint())
        self.updateGeometry()
        
    
    def get_table(self,kind):
        if kind=='part':
            return self.part_widget
        else:
            return self.config_widget
    
    def setRow(self, kind, row_index, data):
        self.get_table(kind).rows[row_index].set_data(data)
    def addRow(self, kind, data=None):
        table = self.get_table(kind)
        table.add()
        if data:
            self.setRow(kind,len(table.rows)-1,data)
    
    def loadExample(self,en=None):
        # not good practice to find main this way?  but eventually
        # loadExample will be removed
        m = self.mode.main
        if not m.designs():
            m.addDesign("unnamed")
        
        with signalsBlocked(self.part_widget,self.config_widget,self.tr_w):
            self.part_widget.clear()
            self.config_widget.clear()
            
            if en is None:
                dlg = QInputDialog(self)
                dlg.setInputMode(QInputDialog.TextInput)
                dlg.setLabelText('1  -  Single Condition Block Design \n2  -  Two Condition Block Design \n3  -  Single Condition Event Related \n4  -  Two Condition Event Related \n5  -  Three Condition Event Related')
                dlg.setWindowTitle('Enter 1-5')
                dlg.resize(100,300) 
                appendStyleSheet(dlg,'''
                    .QLineEdit {
                        background: #ffffff;
                        margin-right: 100px;
                        margin-left: 100px;
                        margin-bottom: 10px;
                        border: 1px solid #000000;
                        qproperty-alignment: AlignCenter;
                    }
                    .QPushButton {
                        background-color: #cccccc;
                        font: normal 12px;
                        border-style: outset;
                        border-width: 1px;
                        border-radius: 4px;
                        border-color: black;
                        width: 50px;
                        height: 12px;
                        padding: 4px;
                        margin: 6px;
                    }
                    .QPushButton:pressed {
                        background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #999999, stop:1 #a6a6a6)
                    }
                    .QLabel {
                        background: #ffffff;
                        margin: 6px;
                        padding: 8px;
                        border: 1px solid #000000;
                        border-radius: 4px;
                    }
                    QWidget {
                        border: 0px;
                    }
                ''')                           
                ok = dlg.exec_()                                
                en = dlg.textValue()
                #(en,ok) = QInputDialog.getText(self, 'Enter 1-5', '1 - Single Condition Block Design \n2 - Two Condition Block Design \n3 - Single Condition Event Related \n4 - Two Condition Event Related \n5 - Three Condition Event Related')
                if ok:
                    en = int(en)
                    self.tr_w.setText(str('2.5'))
                else:
                    en = 0
            
            #NOTE: the difficulty I had making these class examples was that the goal was to show how block designs work
            # but under the assumption that there are underlying trials (multiple per block).  Did not have a mode yet for
            # simulating by one model and evaluating with another model.  So I hacked in things like nested modeled events...
            # now a proper simulation mode is planned, so designs like this should be trashed soon.
            if en==1:
                # Single condition blocked design
                self.addRow('part', dict(name='run', components=['block']))
                self.addRow('part', dict(name='block', components=['stimulus'], types=['face']))
                self.addRow('config', dict(name='run',model='', N=1,post=10))
                self.addRow('config', dict(name='block', model='dmBLOCK(1)',regression_mode='AM1', N=4, inter=10))
                self.addRow('config', dict(name='stimulus', N=10, dur=1,model=''))
                '''
                class
                self.addRow('part', dict(name='run', components=['block']))
                self.addRow('part', dict(name='block', components=['stimulus'], types=['face']))
                self.addRow('config', dict(name='run',model='', N=1))
                self.addRow('config', dict(name='block', model='BLOCK(1,10)', N=4, post=10))
                self.addRow('config', dict(name='stimulus', N=10, dur=1, model='BLOCK(1,1)'))
                s = self.state.experiment_settings
                s['metric'] = 'face.block'
                s['iterations']=16
                '''
            if en==2:
                # Double condition blocked design
                self.addRow('part', dict(name='run', components=['block']))
                self.addRow('part', dict(name='block', components=['stimulus'], types=['face','scramble']))
                self.addRow('config', dict(name='run',model='', N=1,post=10))
                self.addRow('config', dict(name='block', model='dmBLOCK(1)', N=4, inter=10, max_consec=1, regression_mode='AM1'))
                self.addRow('config', dict(name='stimulus', N=10, dur=1,model=''))
                
                '''
                class
                self.addRow('part', dict(name='run', components=['block']))
                self.addRow('part', dict(name='block', components=['stimulus'], types=['face','scramble']))
                self.addRow('config', dict(name='run',model='', N=1))
                self.addRow('config', dict(name='block', model='BLOCK(1,10)', N=4, post=10, max_consec=1))
                self.addRow('config', dict(name='stimulus', N=10, dur=1, model='BLOCK(1,1)'))
                s = self.state.experiment_settings
                s['metric'] = 'face.block+scramble.block'
                s['iterations']=16
                '''
            if en==3:
                # Single condition event design
                self.addRow('part', dict(name='run', components=['trial']))
                self.addRow('part', dict(name='trial', components=['stimulus','iti'], types=['face']))
                self.addRow('config', dict(name='run', model='', N=1,post=10))
                self.addRow('config', dict(name='trial', model='', N=4))
                self.addRow('config', dict(name='stimulus', model='dmBLOCK(1)', dur=1, regression_mode='AM1'))
                self.addRow('config', dict(name='iti', model='',dur=25))
                '''
                s = self.state.experiment_settings
                s['metric'] = 'face.stimulus'
                s['iterations']=16
                '''
            if en==4:
                # Double condition event design
                self.addRow('part', dict(name='run', components=['trial']))
                self.addRow('part', dict(name='trial', components=['stimulus','iti'], types=['face','scramble']))
                self.addRow('config', dict(name='run', model='', N=1,post=10))
                self.addRow('config', dict(name='trial', model='', N=8, max_consec=2))
                self.addRow('config', dict(name='stimulus', model='dmBLOCK(1)', dur=1, regression_mode='AM1'))
                self.addRow('config', dict(name='iti', model='',dur=25))
                '''
                s = self.state.experiment_settings
                s['metric'] = 'face.stimulus+scramble.stimulus'
                s['iterations']=16
                '''
            if en==5:
                self.addRow('part', dict(name='run', components=['trial']))
                self.addRow('part', dict(name='trial', components=['stimulus','iti'], types=['face','scramble','puppies']))
                self.addRow('config', dict(name='run', model='', N=1,post=10))
                self.addRow('config', dict(name='trial', model='', N=60, max_consec=3))
                self.addRow('config', dict(name='stimulus', model='dmBLOCK(1)', dur=1, regression_mode='AM1'))
                self.addRow('config', dict(name='iti', model='',dur=Dist.Exp(2,3.5,6)))
        self.mode.onTableEdit()
    
    def enableRevert(self,enabled=True):
        '''
        A Design only holds onto details associated with a valid design.  So if the
        user types up an invalid design via the GUI the displayed (incorrect) values will no
        longer reflect he actual (valid) design as is stored.  If they were to
        switch to a different design or mode, internally the best way to proceed would be to
        drop all the invalid changes and keep the most recent valid design.  Important to 
        make this b\ehavior clear to the user!
        
        If there is something wrong with the specified design, user will be able to 
        directly revert to the last valid configuration.  Else they'll get a warning
        if trying to unfocus an invalid configuratino (see Main.leavingCurrentDesig).
        
        
        '''
        self.revert_w.setEnabled(enabled)

    def hclick(self):
        if os.path.isdir(os.path.join(os.path.expanduser('~'),'.DesignExplorer/docs/manual')):
            self._doc_folder = os.path.join(os.path.expanduser('~'),'.DesignExplorer/docs/manual')
        else:
            self._doc_folder = os.getcwd()+'/docs/manual'
            
        filepath = self._doc_folder+'/explorer_manual.pdf'
        if sys.platform.startswith('darwin'):
            subprocess.call(('open', filepath))
        elif os.name == 'nt':
            os.startfile(filepath)
        elif os.name == 'posix':
            subprocess.call(('xdg-open', filepath))


class DesignMode(BaseMode):
    title = 'Design'
    toolTip = 'Define and configure events'
    @perr
    def __init__(self,main):
        BaseMode.__init__(self,main)
        self.status_catch = StatusCatch(self.main.setStatus)
        self.design = None
        
    @perr
    def addedToMain(self):
        d = self.main.focusedDesign()
        
        self.vis
        
        self._setDesign(self.main.focusedDesign())
        
    @perr
    def makeWidget(self):
        return DesignModeWidget(self)
    @perr
    def designFocused(self,design,**kwargs):
        self._setDesign(design)
    @perr
    def _setDesign(self,design):
        self.design = design
        self.widget.load(design)
        self.widget.enableRevert(False)
        self.saveOrdering()
        # there are no changes yet so don't refresh.  else you get unnecessary
        # designReconfigured notifications
        #self.refresh()
    @property
    def vis(self):
        # DesignMode is unique in that it currently forces a single Visualization.
        # would be better (more elegant) to support disabling of the close button or something.
        # in fact...
        #impl: this forced auto-resurrecting visualization should be improved eventually..
        return self.main.activateVisualization(DesignModeVisualization)
    
    #opt: now that usning reconfig rather than "restart",
    # should take advantage of more specific callbacks (tr, config, parts)
    # like visualizeMode now does.
    def onTrEdit(self):
        dout('tr')
        self.refresh()
    def onTableEdit(self):
        self.refresh()
    def onError(self):
        if self.design.valid():
            self.widget.enableRevert(True)
            self.main.appendStatus('click "revert" to go back to the previous valid settings')
        else:
            self.widget.enableRevert(False)
            self.main.appendStatus("you must fix the settings before moving on, else they'll be discarded")
    def onSuccess(self):
        self.main.setStatus("successful")
        self.saveOrdering()
        self.widget.enableRevert(False)
    @perr
    def refresh(self):
        # to be called whenever the user changes some aspect of the current design
        design = self.design
        
        # always save the ordering
        #self.saveOrdering()
        
        # extract part details
        with self.status_catch('error in parts table:') as err:
            part_list = self.widget.part_widget.parse()
        if err:
            return self.onError()
        
        # extract config details
        with self.status_catch('error in config table:') as err:
            config = self.widget.config_widget.parse()
        if err:
            return self.onError()
        
        # originally used for debugging.  this shows how to create the same design
        # programatically using StimSim (partially)
        '''
        lines=[]
        for part in part_list:
            subparts=str(part.parts)[1:-1]
            if subparts.endswith(','):
                subparts=subparts[:-1]
            lines.append('part_{} = Part("{}", {}, types={})'.format(part.name,part.name,subparts,part.types))
        for name in config:
            lines.append('config["{}"] = {}'.format(name,config[name]))
        '''
        
        tr = float(self.widget.tr_w.text()) # must be valid, it has a validator attached.
        with self.status_catch as err:        
            design.reconfig(part_list, config, tr)
        if err:
            return self.onError()
        self.onSuccess()
    
    def saveOrdering(self):
        # just for convenience, keeps track of the part/config table order.  Internally
        # this order is meaningless, but it could matter to the user so we try to save/restore
        # it throughout.
        if self.design:
            self.design.userOrdering('design_parts',self.widget.part_widget.getNames())
            self.design.userOrdering('design_config',self.widget.config_widget.getNames())
    
    def onRevertClicked(self):
        assert(self.design.valid())
        self.widget.load(self.design)
        self.onSuccess()

'''
#clean: I fixed this already, right?


mystery

_get_all_timings fails to get the correct modeled event names.  because 
for some reason rests are given the same model as their associated event??
    [(name,ie.parts.get_config(name).model) for name in ie._all_onsets]
    [('face.stimulus', ''),
     ('rest.inter.block.block', 'dmBLOCK(1)'),
     ('face.block', 'dmBLOCK(1)')]

yet if I generate() as normal, I get the event names correctly via stim paths...

rest type takes this as its full name:
    'rest.'+type+'.'+name
    
the depth priority config stumbles here because the suffix does match something...

however, only the hacked in _get_all_timings nonsense uses get_config (or config[])
on potential rest events.  a bit brittle, but ...
    plots also use it
    
    need _all_onsets, _all_durations [those are fine]
    _event_names is the tricky part.

'''