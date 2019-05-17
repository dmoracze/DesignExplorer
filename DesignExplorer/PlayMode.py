from __future__ import absolute_import
from .common import *

assert(False) #impl: early draft, likely does not meet current interface requirements,
# and never finished.  don't try to use this yet.

# for now, there is only one visualization.  So it is simpler to have the Mode know about it
# and interact with it more directly.  so not using onModeMessage and such.
class PlayModeVisualization(BaseVisualization):
    def __init__(self,main):
        BaseVisualization.__init__(self,main)
        
        self._noise_mean = 0
                
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
    
    def setDesign(self,design):
        self.design = design
        if design is None:
            self.ax.clear()
            return
        self.mode = self.main.getMode()
        x1D = design.x1D()
        
        self.N = len(x1D.column)
        self.NT = len(x1D.column[0])
        self.est_signals = [np.zeros(self.NT) for i in range(self.N)]
        self.est_signal = np.zeros(NT)
        self._true_betas = np.zeros(self.N)
        self._betas = np.zeros(self.N)
        
        self.est_signal_lines = []
        t = np.arange(self.NT)*design.tr()
        
        for i in range(self.N):
            #name = x1D.BasisName[i] # not used?
            style = dict()
            
            style.setdefault('linestyle','--')
            style.setdefault('linewidth',3)
            
            self.est_signal_lines.append(self.ax.plot(t,self.est_signals[i],**style)[0])
        
        self.sim_signal_line = ax.plot(t, self.est_signal, label = 'simulated', lw=8, marker='x', markersize=12, markeredgewidth=5, markerfacecolor=None, color='grey')[0]
        self.est_signal_line = ax.plot(t, self.est_signal, label = 'estimated', lw=4, marker='o', markersize=4, markeredgewidth=5, markerfacecolor='k', color='black')[0]
        
        self.ax.legend()
        
        self._signal_ylock = axisLimitLock(self.ax,'y')
        self._junk = axisLimitRules(self.ax,'x',0,NT*design.tr(),1)
        
        # mode has updated for the new design already, so ask for its settings to get started.
        # afterwards, it'll be done from mode's callbacks
        
        #opt: overhead with extra updateLimit and math.  but shouldn't be a problem
        self.setSimSignal(self.mode.getTrueBetas(),self.mode.getNoise())
        for i in range(self.N):
            self.setBeta(i,self.mode.getBeta(i))
    def designFocused(self,design,**kwargs):
        self.setDesign(design)
    # can ignore all other messages as there is no editing of designs in this Mode.    
    
    '''
    set real betas all at once
    set estimated betas individually
    change noise
    
    '''
    def setSimSignal(self,betas,noise):
        self._true_betas = betas
        self._noise = noise
        y = self.design.simulate(betas, noise = noise)
        self.sim_signal_line.set_ydata(y)
        self.updateLimit()
        
    def setTrueBetas(self,betas):
        self.setSimSignal(betas,self._noise)
    def setNoise(self,noise):
        self.setSimSignal(self._true_betas,noise)
    def setBeta(self,i,beta):
        self._betas[i] = beta
        self.est_signal -= self.est_signals[i]
        self.est_signals[i] = self.design.x1D().column[i]*beta
        self.est_signal += self.est_signals[i]
        
        self.est_signal_line.set_ydata(self.eest_signal)
        self.est_signal_lines[i].set_ydata(self.est_signals[i])
        
        fast_redraw(self.ax)
        self.updateLimit()
    
    def updateLimit(self):
        self._signal_ylock.unlock()
        (lo,hi) = self.ax.get_xlim()
        tight_limits(ax=self.ax)
        self._signal_ylock.lock()
        self.ax.set_xlim(lo,hi)
    #def setNoise(se)
        
    
    
    
    


class PlayModeWidget(QWidget):
    def __init__(self,mode,design):
        self.mode = mode
        
        new_but = QPushButton()
        new_but.setText("new game")
        new_but.clicked.connect(mode.onNewGame)
        
        reveal_but = QPushButton()
        reveal_but.setText("reveal")
        reveal_but.clicked.connect(self.revealAnswer)
        
        self.tol_giz = Gizmo('tolerance',w=QSlider(Qt.Horizontal),val=5)
        self.tol_giz.setRange(0,100)
        connect(self.tol_giz,self.onToleranceChange)
        tol = QHBoxLayout()
        tol.addWidget(QLabel('tolerance'))
        tol.addWidget(self.tol_giz.widget)
        self.tol_label = QLabel()
        self.tol_label.setFont(QFont('courier new'))
        tol.addWidget(self.tol_label)
            
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        
        
        buts = QHBoxLayout()
        buts.addWidget(new_but)
        buts.addWidget(restart_but)
        buts.addWidget(reveal_but)
        buts.addLayout(tol)
        
        gl = QGridLayout()
        self.grid=[]
        names = design.eventNames()[0]
        for i,name in enumerate(names):
            w = ArtistStyleWidget(label=name, **design.style(name))
            gl.addWidget(w,0,i)
            
            g1 = Gizmo('',w=QLabel(), val='?')
            gl.addWidget(g1.widget,1,i)
            
            g2 = Gizmo('', w=QLabeledSlider(Qt.Horizontal), val=50, cb = lambda v,i=i: self.onBetaChange(i,v))
            g2.widget.setRange(0,100)
            gl.addWidget(g2.widget,2,i)
            
            self.grid.append((g1,g2))
        
        lay = QVBoxLayout()
        lay.addLayout(gl)
        lay.addWidget(sep)
        lay.addLayout(buts)
        
        h = QHBoxLayout()
        h.addWidget('Noise sdev:')
        self.noise_giz = Gizmo('sdev',w=QLineEdit(), val=1, cb = self.onChangeNoise)
        h.addWidget(self.noise_giz.widget)
        vsep = QFrame()
        vsep.setFrameShape(QFrame.VLine)
        buts.addWidget(vsep)
        buts.addLayout(h)
        
        lay.addStretch()
        self.setLayout(lay)
        
        self.setWinStyle(False)
        
        
    def onBetaChange(self,i,v):
        #self.grid[i][0].value = v # no, these are not indicators for the slider value but rather the true beta labels
        self.mode.onBetaChange(i,v)
    def getBeta(self,i):
        return float(self.grid[i][1].value)
    
    def onChangeNoise(self,v):
        self.mode.onNoiseChange(float(v))
    def getNoise(self):
        return float(self.noise_giz.value)
        
    def onToleranceChange(self,v):
        self.tol_label.setText(str(v))
        self.mode.checkProgress()
    def getTolerance(self):
        return self.tol_giz.value
    
    def revealAnswer(self):
        for i,beta in enumerate(self.mode.getTrueBetas()):
            self.grid[i][0].value = beta
    def hideAnswer(self):
        for i in range(self.mode.N):
            self.grid[i][0].value = "?"

    
    def setWinStyle(self,won):
        if won:
            self.revealAnswer()
            #impl: some sort of color change?  before it was on the plots though...
            #self.fw.fig.set_facecolor("#CCFFCC")
            #self.fw.fig.canvas.draw()
        else:
            self.hideAnswer()
            #impl: back to normal colors.
            
        

class PlayMode(BaseMode):
    title='Betas Game'
    def __init__(self,main):
        BaseMode.__init__(self,main)
    
    @property
    def vis(self):
        return self.main.activateVisualization(PlayModeVisualization)
    
    def addedToMain(self):
        d = self.main.focusedDesign()
        self.vis
        self.setDesign(d)
    def designFocused(self,design,**kwargs):
        self.setDesign(design)
    
    def setDesign(self,design):
        self.design = design
        if design is None:
            self.widget = self.main.setModeWidget(w)
            return
        
        self.N = len(design.eventNames()[0])
        self.widget = self.main.setModeWidget(PlayModeWidget(self,design))
        self.vis.setDesign(design)
    
    def getBeta(self,i):
        return self.widget.getBeta(i)
    def getNoise(self):
        return self.widget.getNoise()
    def getTrueBetas(self):
        return self._true_betas
    def getBetas(self):
        return np.array([self.getBeta(i) for i in range(self.N)])
    def getTolerance(self):
        return self.widget.getTolerance()
        
    def onBetaChange(self,i,value):
        self.vis.setBeta(i,value)
        self.checkProgress()
    def onNoiseChange(self,value):
        self.vis.setNoise(value)
        self.checkProgress()
    
    def onNewGame(self,event):
        self.restart()
    
    def restart(self):
        self.won = False
        self.widget.setWinStyle(False)
        self._true_betas = np.random.randint(0,100,self.N)
        self.vis.setTrueBetas(self._true_betas)
        self.checkProgress()
    
    def checkProgress(self):
        if not self.won:
            err = (self.getTrueBetas() - self.getBetas()).abs().max()
            if err <= self.getTolerance():
                self.won = True
                self.widget.setWinStyle(True)
    
        
    

        
        
        