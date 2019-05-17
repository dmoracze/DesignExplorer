from __future__ import absolute_import
from .common import *
from collections import defaultdict

from .SimulateMode import SimulatedSignalVisualization


      


class SimpleAllSelectedVisualization(BaseVisualization):
    title = 'invalid visualization'
    def __init__(self,main):
        BaseVisualization.__init__(self,main)
        self.init()
        self._update()
    
    def init(self):
        pass
    def clear(self):
        pass
    def update(self,designs):
        pass
    
    def _update(self):
        designs = [d for d in self.main.selectedDesigns() if d.valid()]
        
        #self.designs = designs
        #self.names = [d.name for d in design]
        if not designs:
            self.clear()
            return
        '''
        #fixme: this is a temporary measure to ensure that
        # the visualizations don't raise exceptions when
        # encountering dissimilar designs.  I don't want
        # this to be the final solution to the problem.
        groups = defaultdict(list)
        for d in designs:
            groups[d.eventNames()[0]].append(d)
        N=-1
        for g in groups.values():
            if len(g)>N:
                N=len(g)
                designs=g
        '''
        
        self.update(designs)
    
    def designFocused(self,design,**kwargs):
        pass #idea: could highlight the focused design
    def designDeselected(self,design,**kwargs):
        self._update()
    def designChanged(self,design):
        if not design.selected:
            return
        self._update()
    def _getDefaultName(self):
        return self.title
    
    # most visualizations don't need any of this, so 
    # convenient to disable in base class
    def designExtraChanged(self,design,what=None,**kwargs):
        pass

class SimpleFigureV(SimpleAllSelectedVisualization):
    def init(self):
        self.fw = FigureWidget()
        self.f = self.fw.fig
        self.ax = self.f.add_subplot(1,1,1)
        self.widget.setWidget(self.fw)
    def clear(self):
        self.ax.clear()
    def _update(self):
        self.clear()
        super(SimpleFigureV,self)._update()
        self.fw.fig.tight_layout()
        self.fw.redraw()
        
'''
# old version didn't do well preserving the previous orders
def unionValues(namess,valuess,missing=np.nan):
    ret_names=set([])
    for names in namess:
        ret_names.update(names)
    ret_names=list(ret_names)
    print(namess)
    print(ret_names)
    N = len(ret_names)
    ret_valuess=[]
    for names,values in zip(namess,valuess):
        temp=[missing]*N
        for name,value in zip(names,values):
            temp[ret_names.index(name)] = value
        ret_valuess.append(temp)
    return ret_names,ret_valuess
'''
def unionValues(namess,valuess,missing=np.nan):
    '''
    
    '''
    ret_names=[]
    for names in namess:
        for name in names:
            if name not in ret_names:
                ret_names.append(name)
    
    print(namess)
    print(ret_names)
    N = len(ret_names)
    ret_valuess=[]
    for names,values in zip(namess,valuess):
        temp=[missing]*N
        for name,value in zip(names,values):
            temp[ret_names.index(name)] = value
        ret_valuess.append(temp)
    return ret_names,ret_valuess

class VifVisualization(SimpleFigureV):
    title = 'Variance Inflation Factor'
    def update(self,designs):
        (labels,values) = unionValues([d.eventNames(baseline=True)[0] for d in designs], [d.vif() for d in designs])
        jk.bar(values, labels=labels, sublabels=[d.name for d in designs], ax=self.ax)
        
class MetricQualityVisualization(SimpleFigureV):
    title = 'Quality Metric'
    def update(self,designs):
        values = [d.quality() for d in designs]
        names = [d.name for d in designs]
        lefts = np.arange(len(names))
        self.ax.barh(lefts,values)
        self.ax.set_yticks(lefts+0.5)
        self.ax.set_yticklabels(names,va='center')
        if np.isinf(values).any:
            dout('quality metric not defined for some designs!')


class SimpleDfV(SimpleAllSelectedVisualization):
    def init(self):
        self.dfw = DataFrameWidget()
        self.widget.setWidget(self.dfw)
    def update(self,designs):
        dfs = [getattr(d,self.attr)() for d in designs]
        df = pd.merge(dfs, on=self.on, suffixes=[d.name for d in designs], force_suffixes=True, how='outer')
        self.dfw.setDataFrame(df)
    def clear(self):
        self.dfw.setDataFrame(pd.DataFrame())

class ColinearityVisualization(SimpleDfV):
    title='Collinearity'
    attr='colinearity'
    on=('A','B')
class NsdVisualization(SimpleDfV):
    title='Normalized Standard Deviation'
    attr='qualities'
    on='label'


class VisualizeModeWidget(QWidget):
    def __init__(self,mode):
        QWidget.__init__(self)
        self.mode = mode

        lay = QVBoxLayout()             # overall
        vis_lay = QVBoxLayout()         # plots
        opt_lay = QHBoxLayout()         # layout for options
        lmet_lay = QVBoxLayout()        # left metric options
        rmet_lay = QVBoxLayout()        # right metric options
        lower_lay = QHBoxLayout()       # entire lower display (below config table)
        lower_lay.addLayout(opt_lay)    # options layout
        lower_lay.addLayout(vis_lay)    # visualization layout
    
        # create coonfig table
        editable = [col not in ('name',) for col in ConfigTable.col_names]
        self.config_widget = ConfigTable(self,  editable=editable)
        for name in ('type','dist','copy','remove'):
            i = ConfigTable.col_names.index(name)
            self.config_widget.setColumnHidden(i,True)
        #clean: would like a simple disable option for the base class
        self.config_widget.setDragEnabled(False)
        self.config_widget.setAcceptDrops(False)
        self.config_widget.viewport().setAcceptDrops(False)
        self.config_widget.setSizePolicy(QSizePolicy.MinimumExpanding,QSizePolicy.MinimumExpanding)

        # add the buttons
        def add(lay,txt,typ,tip,**kwargs):
            b = QPushButton()
            b.setText(txt)
            connect(b.clicked, lambda arg: self.mode.main.activateVisualization(typ,**kwargs))
            g = Gizmo(w=b)
            g.widget.setToolTip(tip)
            g.widget.setStyleSheet('''
                .QPushButton {
                background-color: #cccccc;
                font: normal 12px;
                border-style: outset;
                border-width: 1px;
                border-radius: 4px;
                border-color: black;
                width: 175px;
                height: 15px;
                padding: 4px;
                margin: 4px
                }
                .QPushButton:pressed {
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #999999, stop:1 #a6a6a6)
                }
            ''')
            lay.addWidget(g.widget)

        add(lmet_lay,'Collinearity',ColinearityVisualization, tip='Colinearity table by design')
        add(lmet_lay,'Variance Inflation Factor',VifVisualization, tip='Graph of VIF by design')
        opt_lay.addLayout(lmet_lay)
        opt_lay.addStretch()
        add(rmet_lay,'Metric Quality',MetricQualityVisualization, tip='Graph of metric quality by design')
        add(rmet_lay,'Normalized Standard Deviation',NsdVisualization, tip='Normalized standard deviation table by design')
        opt_lay.addLayout(rmet_lay)
        opt_lay.addStretch()
        add(opt_lay,'View Ideal Signal',SimulatedSignalVisualization,simple=True, tip='View ideal BOLD signal')
        opt_lay.addStretch()

        # TR mini widget
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

        # help button
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

        # revert button
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

        # TR layout
        tr_lay = QHBoxLayout()
        tr_lay.addWidget(tr_lab)
        tr_lay.addWidget(self.tr_w)
        tr_lay.setSpacing(8)

        # put options together
        opt_lay.addLayout(tr_lay)
        opt_lay.addStretch()
        opt_lay.addWidget(r)
        opt_lay.addStretch()
        opt_lay.addWidget(help_button)

        # assemble entire widget
        lay.addWidget(self.config_widget)
        lay.addLayout(lower_lay)
        self.setLayout(lay)
        
        connect(help_button.clicked, lambda unused: self.hclick())
        connect(self.config_widget.tableDataChanged, self.mode.onTableEdit)
        connect(self.tr_w.textChanged,lambda unused: self.mode.onTrEdit())
        connect(self.revert_w.clicked,lambda unused: self.mode.onRevertClicked())
    
    #style: should load emit or not?  in a base clase I have it emitting, here I do not...
    def load(self,design):
        with signalsBlocked(self.config_widget, self.tr_w):
            if design and design.valid():
                self.config_widget.load(design)
                self.tr_w.setText(str(design.tr()))
                self.tr_w.setEnabled(True)
                
                (modeled_event_names,_) = design.eventNames()
                for row in self.config_widget.rows:
                    if row['name'] in modeled_event_names:
                        self.config_widget.setRowHidden(row.get_index(),True)
            else:
                self.config_widget.clear()
                self.tr_w.setText("")
                self.tr_w.setEnabled(False)
    
    def enableRevert(self,enabled=True):
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

        

class VisualizeMode(BaseMode):
    '''
    promises not to change the parts of a Design (just config and tr)
    '''
    title='Visualize'
    toolTip='View ideal BOLD signal and quality metrics'
    def __init__(self,main):
        BaseMode.__init__(self,main)
        self.status_catch = StatusCatch(self.main.setStatus)
        self.design = None
    def makeWidget(self):
        return VisualizeModeWidget(self)
    def addedToMain(self):
        d = self.main.focusedDesign()
        self._setDesign(d)
    def designFocused(self,design,**kwargs):
        self._setDesign(design)
    def _setDesign(self,design):
        self.design = design
        self.widget.load(design)
        self.widget.enableRevert(False)
    
    def onError(self):
        if self.design.valid():
            self.widget.enableRevert(True)
            self.main.appendStatus('click "revert" to go back to the previous valid settings')
        else:
            self.widget.enableRevert(False)
            self.main.appendStatus("Very sorry, you must delete this design... it is very very broken...")
    def onSuccess(self):
        self.main.setStatus("")
        self.widget.enableRevert(False)
    
    def _refresh(self,**kwargs):
        with self.status_catch as err:
            self.design.reconfig(**kwargs)
        if err:
            return self.onError()
        
        return self.onSuccess()
    
    def onTableEdit(self):
        with self.status_catch('error in config table:') as err:
            config = self.widget.config_widget.parse()
        if err:
            return self.onError()
        self._refresh(config=config)
    def onTrEdit(self):
        dout('tr')
        self._refresh(tr=float(self.widget.tr_w.text()))
    
    def onRevertClicked(self):
        # reloads the design, discarding invalid changes
        assert(self.design.valid())
        self.widget.load(self.design)
        self.onSuccess()
        
        
        
