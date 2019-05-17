from __future__ import absolute_import
from .common import *


class Simulation(object):
    def __init__(self,sim_design,est_design,N,NG,betas,beta_noise,noise):
        '''
            Simple class to run a simulation , deconvolve the simulated data, and store all the details.
            
            if NG>1, then the results will be presented in a group level analysis style.  groups of NG
            simulated and recovered betas will be averaged, so that each entry in betas_out represents
            the group average for one simulated group.  Note that noisy_parts, noisy, and y will have
            length NG*N because group level happens after deconvolution and grouping these wouldn't make
            as much since.
        '''
        # save some basic details
        self.betas_in=betas
        self.sim_design=sim_design
        self.est_design=est_design
        self.N=N
        self.NG=NG
        self.NT = sim_design.nt()
        self.t = np.arange(sim_design.nt())*sim_design.tr()
        
        # simulate signals
        (y,self.ideal,noisy_parts,self.ideal_parts,noisy_betas) = sim_design.simulate(N=N*NG,betas=betas,beta_noise=beta_noise,noise=noise,split=True)
        self.betas_out = est_design.deconvolve(y)
        
        # group level analysis
        if self.NG!=1:
            self.betas_out = np.reshape(self.betas_out,(NG,N,-1)).mean(0)
        
        # these will have length N*NG, hopefully this isn't a problem elsewhere?
        self.noisy_parts = noisy_parts
        self.noisy = self.y = y
        
        

class Labeled(QWidget):
    '''
    simple QWidget that wraps given widget together
    with a QLabel (or if txt isn't a string, then
    txt is added directly rather than being made into
    a QLabel).
    
    label and widget are attributes you can read.
    '''
    def __init__(self,txt,*widgets):
        QWidget.__init__(self)
        if isinstance(txt,basestring):
            label = QLabel(txt)
        else:
            label = txt
        
        self.label = label
        self.widgets = widgets
        
        lay = QHBoxLayout()
        lay.addWidget(label)
        for w in widgets:
            lay.addWidget(w)
            lay.addStretch()
        self.setLayout(lay)

#idea: a single helper class to apply all the conveniences
# I've implemented already for figures.  limit locks,
# panning, movable legends, fast redrawing, 
# maybe legend-based toggling and hover callbacks?
# also context menues and saving figures

#clean: repeated code (at least the figure widget stuff)
# could use multiple inheritance but... ick...  rarely works properly
class SimulatedSignalVisualization(SingleDesignFigureVisualization):
    title = 'Signal'
    def __init__(self,main,only_focused=False, simple=False):
        SingleDesignFigureVisualization.__init__(self,main,only_focused=only_focused)
        self._simple = simple
        self._line = None
        self._component_lines = None
        self._ylock = axisLimitLock(self.ax,'y',width=None)
        self._xlock = axisLimitLock(self.ax,'x',width=1)
        self.allowPanning()
        self.refresh()
    def update(self,design):
        if not design or not design.valid() or not design._exp.folder:
            raise RuntimeError('failed folder')
        if self._simple:
            sim = design.simulate(split=True)
        else:
            sim = design.simulate(design.beta(),beta_noise=design.noise(),noise=design.globalNoise(), split=True)
        
        y = sim[0]
        parts = sim[2]
        
        # unlock
        self._ylock.unlock()
        self._xlock.unlock()
        # zoom out
        
        (xlo,xhi) = (0,design.nt()*design.tr())
        (ylo,yhi) = (np.min(y),np.max(y))
        (ylo2,yhi2) = (np.min(parts),np.max(parts))
        if ylo2<ylo:
            ylo=ylo2
        if yhi2>yhi:
            yhi=yhi2
        # add a 4% buffer for y axis
        b=(yhi-ylo)*.04
        ylo-=b
        yhi+=b
        self.ax.set_xlim(xlo,xhi)
        self.ax.set_ylim(ylo,yhi)
        
        #dout(tight_limits(ax=self.ax))
        # reestablish rules
        self._xlock.lock()
        self._ylock.lock()
        
        #clean: can do it all the same way, no need to handle one line different from the others (just evolved that way...)
        
        #impl: styles!
        
        # update plot data
        if not self._line:
            t = np.arange(design.nt())*design.tr()
            self._line = self.ax.plot(t,y,label='signal')[0]
            
            self._component_lines=[]
            names = design.eventNames()[0]
            for name,part in zip(names,parts):
                line = self.ax.plot(t,part,label=name)[0]
                self._component_lines.append(line)
            
            self.ax.legend()
        else:
            if len(self._line.get_xdata()) != len(y):
                t = np.arange(design.nt())*design.tr()
                self._line.set_xdata(t)
                for line in self._component_lines:
                    line.set_xdata(t)
            
            self._line.set_ydata(y)            
            for line,part in zip(self._component_lines,parts):
                line.set_ydata(part)
            
            fast_redraw(self.ax, copy_legend=True)
        
class SimulationVisualization(BaseVisualization):
    def __init__(self,main,**kwargs):
        BaseVisualization.__init__(self,main)
        self.fw = FigureWidget()
        self.ax = self.fw.fig.add_subplot(1,1,1)
        self.widget.setWidget(self.fw)
        self.cax = ConvenientAxes(self.ax,**kwargs)
        self.onModeMessage('resim')
    
    def _update(self):
        pass
    def update(self):
        pass
    
    def getData(self):
        return self.main.getMode().getSimulationData()
    
    def onModeMessage(self,msg,**kwargs):
        if msg=='resim':
            data = self.getData()
            if not data:
                self.clear()
            else:
                self.update()
        elif msg=='clear':
            self.clear()
        else:
            pass
        self.fw.fig.tight_layout()
        self.fw.redraw()
        
    def clear(self):
        self.cax.clear()

    def _getDefaultName(self):
        return self.title

class SimulationSignalsVisualization(SimulationVisualization):
    title='Simulated Signals'
    def __init__(self,main):
        SimulationVisualization.__init__(self,main,pan=True,limit=True)
    
    def update(self):
        data = self.getData()
        #if not #fixme: what was I doing here?
        self.cax.clear()
        with self.cax as ax:
            if data.N!=1:
                hexbin(data.t,data.y,ax=ax, mincnt=1,cmap=mpl.cm.bone, bins=data.N,gridsize=data.NT)
            ym=np.mean(data.y,0)
            
            ax.plot(data.t,data.ideal,label='ideal',color='blue')
            ax.plot(data.t,ym,label='mean',color='red')
            #ax.plot(np.median(noisy,0),label='median',color='green')
            ax.legend(loc=0,ncol=np.inf)

        
class SimulationBetasVisualization(SimulationVisualization):
    title='Beta Errors'
    def __init__(self,main):
        SimulationVisualization.__init__(self,main,pan=True,limit=True)
    def update(self):
        data = self.getData()
        self.cax.clear()
        est_design = data.est_design
        sim_design = data.sim_design
        beta_errors = data.betas_out-data.betas_in
        
        names = est_design.eventNames()[0]
        
        
        with self.cax(resize=(data.N==1)) as ax:
            if data.N==1:
                beta_errors=beta_errors
                w=0.8
                o=w/2.0
                for i,beta_error in enumerate(beta_errors):
                    r = mpl.patches.Rectangle((i-o,0),width=w,height=beta_error,**est_design.style(i,bar=True))
                    ax.add_artist(r)
            else:
                width = 0.8
                
                sb.violinplot(data=beta_errors,positions=np.arange(len(beta_errors)),ax=ax, names=names, widths=width)
                
                lo=np.min(beta_errors)
                hi=np.max(beta_errors)
                if lo==hi:
                    pass
                else:
                    nbins = freedman_diaconis_bins(beta_errors)
                    bins = np.linspace(lo,hi,nbins)
                    
                    for i,name in enumerate(names):
                        values = beta_errors[:,i]
                        
                        hs = np.histogram(values,bins=bins,density=True)[0]
                        hs*=(width/2.0/np.max(hs))
                        height=bins[1]-bins[0]
                        
                        for (b,h) in zip(bins[:-1],hs):
                            r = mpl.patches.Rectangle((i,b),width=h,height=height,alpha=0.5,color='grey')
                            ax.add_artist(r)
            
            ax.set_ylabel('beta error')
            ticks(names,ax=ax)

class SimulationBetasScatterVisualization(SimulationVisualization):
    title='Beta Error Scatter'
    def __init__(self,main):
        SimulationVisualization.__init__(self,main,pan=True,limit=True)
    def update(self):
        data = self.getData()
        self.cax.clear()
        est_design = data.est_design
        sim_design = data.sim_design
        beta_errors = data.betas_out-data.betas_in

        names = est_design.eventNames()[0]
        
        if len(names)!=2:
            raise NotImplementedError('this visualization only handles designs with 2 modeled events at the moment')
            #impl: a way to pick which events are used for greader than 2 modeled events, maybe more than 2 at a time?
        
        #if data.N==1:
        
        with self.cax(resize=False) as ax:
            x = beta_errors[:,0]
            y = beta_errors[:,1]
            ax.scatter(x,y)
            ax.set_xlabel('{} error'.format(names[0]))
            ax.set_ylabel('{} error'.format(names[1]))
            
            from scipy.stats import linregress
            (s,i,r,p,e) = linregress(x,y)
            ax.plot(x,i+s*x,color='blue',label='slope: {}\npval: {}'.format(s,p))
            #ax.legend()
            
            #print(np.max(np.abs(x)),np.max(np.abs(y)))
            ax.axis('square')

                

'''
axes.relim does basically this, but does not take into account collections.

The only instances when limits aren't automatically updated is if at some point updates
aren't requested (rare?) or if artist data is changed directly without then notifying
the axes.  

only would change the data though for performance increase, so a bit concerned if the mess
of relim is a good idea?  

to support containers... I've not yet found where the limits are calculated.  base class or super class I guess.

'''
def autosize(ax):
    '''
    sets the x and y limits of the given matplotlib axes instance
    to contain all the data.  Because for some reason the various matplotlib
    provided autosize autoscale whatever methods/functions all seem to fail
    at least under some circumstances.  
    
    Makes a union bounding box based on every artist and collection in ax.  actually not collections,
    since I've yet to figure out how to get a real bounding box for them.  so here is yet another
    'solution' that only sometimes works...
    
    not sure if later setting the the data of an artist updates its bounding box or not, should check.
    
    more things to implement here...
        * including specific values
        * convenient ways to choose how to pad (expansions, flat padding, all, xy, some)
        * artists and collections, is there anything else
    '''
    
    boxes = [a.get_bbox() for a in ax.artists]
    #boxes.extend([c.get_clip_box().frozen() for c in ax.collections])
    #boxes.extend([c.get_datalim(c.get_transform()) for c in ax.collections])
    bounds = mpl.transforms.Bbox.union(boxes).expanded(1.05,1.05)
    (xlo,ylo,xhi,yhi) = bounds.extents
    ax.set_xlim(xlo,xhi)
    ax.set_ylim(ylo,yhi)

#idea: for plots that involve time or tr, was useful to have that mouse move callback set status somewhere.



# styled label, noise, beta
# 
class DesignExtraWidget(QWidget):
    extraChanged = pyqtSignal()
    def extraChangeEvent(self):
        #self.value = self._giz.value
        self.value = self._w.value()
        self.extraChanged.emit()
    
    def __init__(self,design,what,i,kind='slider',show_label=True):
        QWidget.__init__(self)
        self._design = design
        self._what = what
        self._i = i
        
        name = design.eventNames()[0][i]
        if kind=='slider':
            w = QLabeledSlider(Qt.Horizontal)
            w.setSizePolicy(QSizePolicy.Maximum,QSizePolicy.Maximum)
        elif kind=='updown':
            w = QSpinBox()
        
        w.setRange(0,100)
        w.setValue(self.value)
        self._w = w
        # annoy: for QSpinBox the wrong callback was chosen in Gizmo...
        # perhaps further evidence that Gizmo is too much work.  Qt should
        # have provided a better interface, but too much work for me to 
        # fix that?  Perhaps easier to just do it all manually...
        #self._giz = Gizmo(w=w,value=self.value,cb=self._cb)
        
        lay = QHBoxLayout()
        # if show_label:
        #     #style = ArtistStyleWidget(**design.style(name))
        #     #style.setSizePolicy(QSizePolicy.Maximum,QSizePolicy.Maximum)
        #     n = QLabel(name)
        #     n.setSizePolicy(QSizePolicy.Maximum,QSizePolicy.Maximum)
        #     lay.addWidget(n)
        #     #lay.addWidget(style)
        lay.addWidget(w)
        if kind !='slider':
            lay.addStretch()
        self.setLayout(lay)
        
        connect(w.valueChanged,self._cb)
    
    def _cb(self,*args,**kwargs):
        self.extraChangeEvent()
    @property
    def value(self):
        return self._design.extra(self._what, self._i)
    @value.setter
    def value(self,v):
        self._design.setExtra(self._what, self._i, v)

#fixme: combining the label and value changer was a bad idea.
# should split things up to be more flexible.  a grid layout would look better
class DesignExtraBlock(QWidget):
    def __init__(self,design,what,name,col,tip,show_label=True):
        QWidget.__init__(self)
        self._design = design
        self._what = what
        self._name = name
        self._col = col

        glay = QGridLayout()
        glay.setContentsMargins(2,0,2,0)
        glay.setSpacing(0)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet('''
            .QFrame {
                border: 1px solid grey;
                margin-bottom: 5px;
            }
        ''')
        n = QLabel(name)
        n.setToolTip(tip)
        n.setAlignment(Qt.AlignCenter)
        n.setStyleSheet('''
            .QLabel {
                font: 14px;
                margin-bottom: 5px;
            }
        ''')
        glay.addWidget(n,0,col)
        glay.addWidget(line,1,col)

        names = design.eventNames()[0]
        self._ws=[]
        for i,name in enumerate(names):
            ind = i+2
            w = DesignExtraWidget(design,what,i)
            w.setToolTip(tip)
            if show_label:
                l = QLabel(name)
                l.setStyleSheet('''
                    .QLabel {
                        font: 10px;
                    }
                ''')
                glay.addWidget(l,ind,0)
            glay.addWidget(w,ind,col)
            self._ws.append(w)
        self.setLayout(glay)
    @property
    def value(self):
        return self._design.extra(self._what)
    @value.setter
    def value(self,v):
        self._design.setExtra(self._what,v)
        
##clean: better base class    

#clean: is it reasonable to have the widget not know its mode?
# ideally it would just emit signals.  But it might be more work
# than is worthwhile?
class SimulateModeWidget(QWidget):
    def __init__(self,mode):
        QWidget.__init__(self)
        self.mode = mode
        self.main = mode.main
        self.sim = None
        self.est = None
        self.focused = None
        appendStyleSheet(self,'''
            QLabel {
                background: #ececec;
            }
            QLineEdit {
                background: #ffffff;
                border: 1px solid #000000;
            }
        ''')
        
        # create layouts
        lay = QVBoxLayout()                                     # overall layout
        gconfig_lay = QGridLayout()                             # layout for global options (number of simulations, TR, etc...)
        self.placeholder = QPlaceholder(default_owns=True)      # placeholder for sliders
        slider_lay = QVBoxLayout()                              # layout for sliders
        slider_lay.addLayout(self.placeholder,1)                # placeholder for viz
        vis_lay = QVBoxLayout()                                 # layout for visualize options
        lower_lay = QHBoxLayout()                               # layout for all lower panel options
        lower_lay.setContentsMargins(15,0,15,0)                 # set some margins for lower panel

        # create vertical divider lines
        vline_1 = QFrame()
        vline_1.setFrameShape(QFrame.VLine)
        appendStyleSheet(vline_1,'''
            .QFrame {
                border: 1px dashed grey;
            }
        ''')
        vline_2 = QFrame()
        vline_2.setFrameShape(QFrame.VLine)
        appendStyleSheet(vline_2,'''
            .QFrame {
                border: 1px dashed grey;
            }
        ''')

        # set up config table
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

        # attach it to layout
        lay.addWidget(self.config_widget)
        lay.addLayout(lower_lay)

        # set up options window
        nl = QVBoxLayout()
        # nl.addStretch()
        gconfig_lay.addLayout(nl,0,0,1,3)

        # number of simulations entry
        l = QLabel('Simulations: ')
        l.setToolTip('Enter number of simulations')
        self._Nw = e = QLineEdit()
        appendStyleSheet(e,'''
            QLineEdit {
                background-color: #ffffff;
                margin-top: 5px;
                margin-bottom: 4px;
                margin-left: 5px;
                margin-right: 5px;
                padding-left: 10px;
                padding-right: 10px;
                padding-top: 2px;
                padding-bottom: 2px;
                max-width: 90px;

            }
        ''')
        e.setText("1")
        e.setValidator(QIntValidator(1,1000000000))
        e.setToolTip('Enter number of simulations')
        e.setAlignment(Qt.AlignCenter)
        gconfig_lay.addWidget(l,0,0)
        gconfig_lay.addWidget(e,0,1)
        
        # group size (# done per # of simulations)
        l = QLabel('Group Size: ')
        l.setToolTip('Does a group level analysis, a group of this size is simulated per simulation')
        self._NGw = e = QLineEdit()
        appendStyleSheet(e,'''
            QLineEdit {
                background-color: #ffffff;
                margin-top: 5px;
                margin-bottom: 4px;
                margin-left: 5px;
                margin-right: 5px;
                padding-left: 10px;
                padding-right: 10px;
                padding-top: 2px;
                padding-bottom: 2px;
                max-width: 90px;

            }
        ''')
        e.setText("1")
        e.setValidator(QIntValidator(1,1000000000))
        e.setToolTip('Enter group size')
        e.setAlignment(Qt.AlignCenter)
        gconfig_lay.addWidget(l,1,0)
        gconfig_lay.addWidget(e,1,1)

        # TR entry
        l = QLabel('Repetition Time: ')
        l.setToolTip('Repetition time (in seconds)')
        self.tr_w = QLineEdit()
        appendStyleSheet(self.tr_w,'''
            QLineEdit {
                background-color: #ffffff;
                margin-top: 5px;
                margin-bottom: 4px;
                margin-left: 5px;
                margin-right: 5px;
                padding-left: 10px;
                padding-right: 10px;
                padding-top: 2px;
                padding-bottom: 2px;
                max-width: 90px;
            }
        ''')
        self.tr_w.setText('2.5')
        self.tr_w.setValidator(QDoubleValidator(0,100,2))
        self.tr_w.setToolTip('Repetition time (in seconds)')
        self.tr_w.setAlignment(Qt.AlignCenter)
        gconfig_lay.addWidget(l,2,0)
        gconfig_lay.addWidget(self.tr_w,2,1)

        self.revert_w = r = QPushButton()
        r.setText('Revert')
        appendStyleSheet(r,'''
            .QPushButton {
                font-size: 12px;
                background-color: #e6e6e6;
                border-style: solid;
                border-width: 1px;
                border-radius: 2px;
                border-color: black;
                width: 50px;
                padding: 2px;
                margin: 2px
            }
            .QPushButton:pressed {
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #999999, stop:1 #a6a6a6)
            }
        ''')
        r.setToolTip('Revert to previous state (if you need to)')
        r.setEnabled(False)
        gconfig_lay.addWidget(r,2,2)

        # add some space...
        nl = QVBoxLayout()
        nl.addStretch()
        gconfig_lay.addLayout(nl,3,0,1,3)

        # choose which design to simulate and evaluate (does this work yet?)
        def add(label,i,tip):
            l = QLabel(label)
            l.setToolTip(tip)
            c = QComboBox()
            c.setToolTip(tip)
            c.setEditable(False)
            c.setStyle(QtGui.QStyleFactory.create('Cleanlooks'))
            c.resize(15,80)
            appendStyleSheet(c,'''
                .QComboBox {
                    background-color: #ffffff;
                    margin-top: 5px;
                    margin-bottom: 4px;
                    margin-left: 5px;
                    margin-right: 5px;
                    padding-left: 10px;
                    padding-right: 10px;
                    padding-top: 2px;
                    padding-bottom: 2px;
                    max-width: 90px;
                }
                .QAbstractItemView {
                    background-color: #ffffff;
                    selection-color: #000000;
                }
            ''')
            b_lay = QHBoxLayout()
            b_lay.addStretch()
            b = QPushButton('Show')
            b.setToolTip('show selected design\'s config table')
            b.setStyleSheet('''
                .QPushButton {
                    font-size: 12px;
                    background-color: #cccccc;
                    border-style: solid;
                    border-width: 1px;
                    border-radius: 2px;
                    border-color: black;
                    width: 50px;
                    padding: 2px;
                    margin: 2px
                    }
                .QPushButton:pressed {
                    background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #999999, stop:1 #a6a6a6)
                    }
                ''')
            b_lay.addWidget(b)
            b_lay.addStretch()
            gconfig_lay.addWidget(l,i,0)
            gconfig_lay.addWidget(c,i,1)
            gconfig_lay.addLayout(b_lay,i,2)
            connect(b.clicked, lambda *unused: self.onShowDesign(c.currentText()) )
            connect(c.currentIndexChanged[str], lambda* unused: self.onDesignSelected() )
            return c

        # add the widgets for simulation and generation    
        self.sim_w = add('Simulate using:',4,tip='Choose design used to simulate BOLD signal')
        self.est_w = add('Evaluate using:',5,tip='Choose design used to evaluate BOLD signal')

        #clean up layout
        nl = QVBoxLayout()
        nl.addStretch()
        gconfig_lay.addLayout(nl,6,0,1,3)
        gconfig_lay.setContentsMargins(0,0,0,0)

        # construct the visualization options
        vis_lay.addStretch()
        h = QGridLayout()

        # global noise parameter
        tip = 'Global noise value (arbitrary units: 0 - 100)'
        l = QLabel('Global Noise: ')
        l.setToolTip(tip)
        self._noise_widget = e = QLineEdit()
        appendStyleSheet(e,'''
            QLineEdit {
                background-color: #ffffff;
                margin-top: 5px;
                margin-bottom: 4px;
                margin-left: 5px;
                margin-right: 5px;
                padding-left: 10px;
                padding-right: 10px;
                padding-top: 2px;
                padding-bottom: 2px;
                max-width: 90px;
            }
        ''')
        e.setFixedWidth(100)
        e.setText('0')
        e.setValidator(QIntValidator(0,100))
        e.setToolTip(tip)
        e.setAlignment(Qt.AlignCenter)
        connect(e.textChanged,self._noiseChanged)

        # add global noise to layout
        h.addWidget(l,0,0)
        h.addWidget(e,0,1)
        
        # global noise mean parameter
        tip = 'Global noise mean (arbitrary units: 0 - 100)'
        lm = QLabel('Global Noise Mean: ')
        lm.setToolTip(tip)
        self._noise_mean_widget = em = QLineEdit()
        appendStyleSheet(em,'''
            QLineEdit {
                background-color: #ffffff;
                margin-top: 5px;
                margin-bottom: 4px;
                margin-left: 5px;
                margin-right: 5px;
                padding-left: 10px;
                padding-right: 10px;
                padding-top: 2px;
                padding-bottom: 2px;
                max-width: 90px;
            }
        ''')
        em.setFixedWidth(100)
        em.setText('0')
        em.setValidator(QIntValidator(0,100))
        em.setToolTip(tip)
        em.setAlignment(Qt.AlignCenter)
        connect(em.textChanged,self._noiseChanged)
        
        # add global noise mean to layout
        h.addWidget(lm,1,0)
        h.addWidget(em,1,1)
        
        # button to run simulation
        b = QPushButton()
        appendStyleSheet(b,'''
                .QPushButton {
                    font-size: 12px;
                    background-color: #d9d9d9;
                    border-style: outset;
                    border-width: 1px;
                    border-radius: 3px;
                    border-color: black;
                    min-width: 120px;
                    padding: 6px;
                    margin: 4px
                    }
                .QPushButton:pressed {
                    background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #999999, stop:1 #a6a6a6)
                    }
                ''')
        b.setText('Run Simulation!')
        b.setToolTip('Select to simulate BOLD signal')
        connect(b.clicked, self.onSimulateClicked)
        h.addWidget(b,2,0)
        
        '''
        #impl: checkbox for auto resim around here?  simple test the layout looked bad so I'll skip it for now.
        c = QCheckBox("auto")
        c.setChecked(True)
        connect(c.clicked,self.onAutoClicked)
        h.addWidget(c)
        '''

        hlay = QHBoxLayout()
        hlay.addStretch()
        hbut = QPushButton('?')
        hbut.setToolTip('Open the user manual')
        appendStyleSheet(hbut,'''
                .QPushButton:pressed {
                    background-color: #66ccff;
                    }
                .QPushButton {
                    font-style: bold;
                    font-size: 11px;
                    color: white;
                    background-color: #0066ff;
                    border-style: outset;
                    border: 1px solid black;
                    padding: 2px;
                    height: 8px;
                    width: 20px;
                    }
                ''')
        hlay.addWidget(hbut)
        hlay.addStretch()
        h.addLayout(hlay,2,1)

        # add help and simulate buttons to layout
        vis_lay.addLayout(h)
        vis_lay.addStretch()

        # set up plot option buttons
        view_opts = QGridLayout()
        view_opts.setContentsMargins(10,0,10,20)
        view_menu = QWidget()
        appendStyleSheet(view_menu,'''
            .QWidget {
                border: 0px;
            }
        ''')
        l = QLabel('View Simulation Results')
        appendStyleSheet(l,'''
            QLabel {
                margin-bottom: 1px;
            }
        ''')
        l.setToolTip('Use these options to choose which plots to view')
        l.setAlignment(Qt.AlignCenter)
        view_opts.addWidget(l,0,0)
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        appendStyleSheet(line,'''
            .QFrame {
                border: 1px solid grey;
                margin-bottom: 5px;
                }
            ''')
        view_opts.addWidget(line,1,0)

        def add(txt,typ,i,tip):
            b = QPushButton()
            b.setStyleSheet('''
                .QPushButton {
                    font-size: 12px;
                    background-color: #d9d9d9;
                    border-style: outset;
                    border-width: 1px;
                    border-radius: 2px;
                    border-color: black;
                    padding: 6px;
                    margin-left: 40px;
                    margin-right: 40px;
                    margin-top: 4px;
                    margin-bottom: 4px;
                    }
                .QPushButton:pressed {
                    background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #999999, stop:1 #a6a6a6)
                    }
                ''')
            b.setText(txt)
            connect(b.clicked, lambda arg: self.mode.main.activateVisualization(typ))
            g = Gizmo(w=b,tip=tip)
            view_opts.addWidget(g.widget,i,0)

        add('Simulated Signal',SimulationSignalsVisualization,2,tip='Select to view simulated signal')
        add('Beta Error',SimulationBetasVisualization,3,tip='Select to view the beta errors from simulation')
        add('Beta Error Scatter',SimulationBetasScatterVisualization,4,tip='Select to view the beta errors from simulation as a scatter plot')
        view_menu.setLayout(view_opts)
        vis_lay.addWidget(view_menu)
        vis_lay.addStretch()

        lower_lay.addStretch()
        lower_lay.addLayout(gconfig_lay)
        lower_lay.addStretch()
        lower_lay.addWidget(vline_1)
        lower_lay.addStretch()
        lower_lay.addLayout(slider_lay)
        lower_lay.addStretch()
        lower_lay.addWidget(vline_2)
        lower_lay.addStretch()
        lower_lay.addLayout(vis_lay)
        lower_lay.addStretch()
        #impl: more!
 
        self.refreshDesignLists()
        self.setLayout(lay)
        
        connect(hbut.clicked, lambda unused: self.hclick())
        connect(self.config_widget.tableDataChanged, self.mode.onTableEdit)
        connect(self.tr_w.textChanged,lambda unused: self.mode.onTrEdit())
        connect(self.revert_w.clicked,lambda unused: self.mode.onRevertClicked())
    
    def _focus(self,design):
        if self.focused == design:
            return
        self.enableRevert(False)
        
        self.focused = design
        with signalsBlocked(self.config_widget, self.tr_w, self._noise_widget):
            if design and design.valid():
                self.config_widget.load(design)
                self.tr_w.setText(str(design.tr()))
                self.tr_w.setEnabled(True)
                (m,v) = design.globalNoise()
                self._noise_widget.setText(str(v))
                self._noise_mean_widget.setText(str(m))
                
                if design==self.sim:
                    (modeled_event_names,_) = design.eventNames()
                    for row in self.config_widget.rows:
                        if row['name'] in modeled_event_names:
                            self.config_widget.setRowHidden(row.get_index(),True)
                
            else:
                self.config_widget.clear()
                self.tr_w.setText("")
                self.tr_w.setEnabled(False)
    
    def _noiseChanged(self,ignored):
        v=int(self._noise_widget.text())
        m=int(self._noise_mean_widget.text())
        self.sim.setGlobalNoise(m,v)
    @property
    def N(self):
        return int(self._Nw.text())
    @property
    def NG(self):
        return int(self._NGw.text())
    
    def focusNone(self):
        self._focus(None)
    def focusSim(self):
        self._focus(self.sim)
    def focusEst(self):
        self._focus(self.est)
    def checkFocus(self):
        if self.focused not in (self.sim,self.est):
            self.focusSim()
    
    def onSimulateClicked(self,unused):
        self.mode.resim()
    def onAutoClicked(self,checked):
        self.mode.setAutoResim(checked)
        
    def _setSimDesign(self,new_sim):
        if new_sim == self.sim:
            return
        self.sim = new_sim
        self._select(self.sim_w,new_sim)
        self.checkFocus()
        
        design = new_sim
        with signalsBlocked(self.config_widget, self.tr_w):
            if design and design.valid():
                self.beta_widget = DesignExtraBlock(design,'beta','Beta Value',1,tip='Change beta value of corresponding event')
                self.noise_widget = DesignExtraBlock(design,'noise','Noise',2,tip='Add event-specific noise',show_label=False)

                lay = QHBoxLayout()
                lay.addWidget(self.beta_widget)
                lay.addWidget(self.noise_widget)

                w = QWidget()
                lay.setContentsMargins(20,20,20,10)
                lay.setSpacing(0)
                w.setStyleSheet('''
                    .QWidget {
                        border: 1px solid #666666;
                        border-radius: 6px;
                        padding: 5px;
                        background: white;
                        margin-top: 10px;
                    }
                    QSlider {
                        background: #ffffff;
                    }
                    QLabel {
                        background-color: #ffffff;
                    }
                ''')
                w.setLayout(lay)
                w.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
                self.placeholder.item = w
            else:
                self.placeholder.item = QLabel('invalid design')
    
    def _select(self,w,d):
        with signalsBlocked(w):
            if not d:
                i=-1
            else:
                i=w.findText(d.name)
            w.setCurrentIndex(i)
            
    def _setEstDesign(self,new_est):
        if new_est == self.est:
            return
        self.est = new_est
        self._select(self.est_w,new_est)
        self.checkFocus()

    def setDesigns(self,new_sim,new_est):
        self._setSimDesign(new_sim)
        self._setEstDesign(new_est)
        
    def enableRevert(self,enabled=True):
        self.revert_w.setEnabled(enabled)
    
    def onShowDesign(self,name):
        d = self.main.findDesign(name)
        if d:
            self.main.focusDesign(d)
    
    def onDesignSelected(self):
        sim_name = self.sim_w.currentText()
        est_name = self.est_w.currentText()
        
        new_sim = self.main.findDesign(sim_name)
        new_est = self.main.findDesign(est_name)
        
        self.mode.setDesigns(new_sim,new_est)
    
    def designFocused(self,d,**kwargs):
        if d==self.sim:
            self.focusSim()
        elif d==self.est:
            self.focusEst()
        else:
            self.focusNone()
    
        
    def refreshDesignLists(self):
        with signalsBlocked(self.sim_w,self.est_w):
            designs = self.main.designs()
            names = [design.name for design in designs]
            for w in (self.sim_w,self.est_w):
                w.clear()
                for name in names:
                    w.addItem(name)
                
            if self.sim not in designs:
                self._setSimDesign(None)
            else:
                self._select(self.sim_w,self.sim)
            
            if self.est not in designs:
                self._setEstDesign(None)
            else:
                self._select(self.est_w,self.est)
    
    def designRenamed(self,design,old_name=None,**kwargs):
        with signalsBlocked(self.sim_w,self.est_w):
            if old_name is None:
                i=--1
            else:
                i = self.sim_w.findText(old_name)
            
            if i==-1:
                self.refreshDesignLists()
            else:
                for w in (self.sim_w,self.est_w):
                    i = w.findText(old_name)
                    w.setItemText(i,design.name)

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

        
        


'''
only the sim_design maps to the sliders
easiest and maybe best for users to allow for browsing however.  separate selection for
the two designs and simulation options
'''
class SimulateMode(BaseMode):
    '''
    promises not to change the parts of a Design (just config and tr)
    '''
    title='Simulate'
    toolTip='Simulate BOLD signal from design'
    def __init__(self,main):
        BaseMode.__init__(self,main)
        self.status_catch = StatusCatch(self.main.setStatus)
        self.sim_design = None
        self.est_design = None
        self._data = None
        #fixme: should be optional
        self._auto_resim = True
    def makeWidget(self):
        return SimulateModeWidget(self)
    def addedToMain(self):
        d = self.main.focusedDesign()
        self.setDesigns(d,d)
        
    def designFocused(self,design,**kwargs):
        self.widget.designFocused(design)
            
    def getSimulationData(self):
        return self._data
    def resim(self):
        self._data = Simulation(self.sim_design,self.est_design,self.widget.N,self.widget.NG,self.sim_design.beta(),self.sim_design.noise(),self.sim_design.globalNoise())
        self.main.modeBroadcast('resim')
        
    def setDesigns(self,sim,est):
        if self.sim_design==sim and self.est_design==est:
            return
        self._data = None
        
        self.sim_design = sim
        self.est_design = est
        self.widget.setDesigns(sim,est)
        
        #fixme: probably should be more tightly controlled by Main.  design_tabs
        # should be protected...  also then add a new property to Design
        # that allows hiding and order changing?
        dt = self.main.design_tabs
        dt.showOnlyTabs([dt.index(sim.name),dt.index(est.name)])
        dt.moveTab(dt.index(sim.name),0)
        dt.moveTab(dt.index(est.name),1)
        
        #if self.main.focusedDesign() not in (sim,est):
        #    self.main.focusDesign(sim)
        
        #self.main.maskDesignTabs(show=[sim,est])
        
        #fixme: doesn't matter yet, but really should disallow
        # hidden designs to be 'selected' or 'focused'?  Right?
        # But for simuate mode it doesn't actually end up mattering.
    
    @property
    def design(self):
        return self.widget.focused
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
        self._maybeAutoUpdate()
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
        #clean: check if this is actually needed.  aren't the previous
        # designs still there?  do I just need to do onSucess?  same with DesignMode.
        self.setDesigns(self.sim_design,self.est_design)
        self.onSuccess()
    
    def designRemoved(self,design,**kwargs):
        self.widget.refreshDesignLists()
    def designAdded(self,design,**kwargs):
        self.widget.refreshDesignLists()
    def designRenamed(self,design,**kwargs):
        self.widget.designRenamed(design,**kwargs)
    
    def designReconfigured(self,design,**kwargs):
        self._maybeAutoUpdate()
    def designExtraChanged(self,design,what=None,**kwargs):
        self._maybeAutoUpdate()
    def _maybeAutoUpdate(self):
        #testing: for now.  should be a good option later
        self._auto_resim = (self.widget.N == 1)
        if self._auto_resim:
            self.resim()
    def setAutoResim(self,enabled):
        self._auto_resim = enabled
        #idea: should it resim immediately if enabled?