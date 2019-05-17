from __future__ import absolute_import
from .common import *

#annoy:  is it something to do with how I add the state constants?
# I had to import inside of Design as well
from .Bases import Design


class OptimizeGUI(BetterDialog):
    '''
    the 'run' button will attempt to optimize the design (see Design.optimize)
    with the given settings. upon success the dialog will auto accept and the given
    design will have been optimized.  On failure, the error message is displayed
    and the user can keep retrying.  The 'cancel' button is always available as well,
    if the user cancels there will be no changes to the given design (and any
    changes they made to the optimization settings will be lost).
    '''
    def __init__(self,design):
        BetterDialog.__init__(self)
        
        self.design = design
        self.setStyleSheet('''
            QToolTip {
                background-color: beige;
                font-size: 10px;
                padding: 2px;
                }
            ''')
        
        top = QFormLayout()
        buts = QVBoxLayout()
        bot = QHBoxLayout()
        layout = QVBoxLayout()
        
        self.status = QTextEdit(self)
        self.status.setToolTip('current status')
        self.status_catch = StatusCatch(self.status.setText, show_traceback=True)
        
        def add(txt,cb,tip):
            b = QPushButton()
            b.setText(txt)
            b.setToolTip(tip)
            connect(b.clicked,cb)
            buts.addWidget(b)
            return b
        
        add('run',self._optimize,tip='Optimize now!')
        self.cancel_button = add('cancel', lambda *unused: self.reject(),tip='Reject!')
                
        self.setting_gizmos=[]
        
        def add(name,var_name,w,*args,**kwargs):
            giz = Gizmo(name,w,*args,**kwargs)
            giz.var_name=var_name
            top.addRow(name,giz.widget)
            self.setting_gizmos.append(giz)
            #return giz.widget
        
        
        add('Fix run lengths', 'fix_run_lengths', QCheckBox(), val=True, tip='Make sure all run lengths are the same')
        add('Include all contrast pairs', 'all_contrast_pairs', QCheckBox(), val=True, tip='All possible contrast pairs will be used')
        w=QSpinBox()
        N=cpu_count()
        w.setMinimum(1)
        w.setMaximum(N)
        w.setValue(N)
        add('Number of threads','nthreads',w,tip='How many threads to use?\nThe more the faster...')
        w=QLineEdit()
        w.setValidator(QIntValidator(1,1000000000))
        w.setText("1000")
        add('Number of iterations','iterations',w,tip='How many iterations do you want?\nThe more the better...',get=Widget.as_int)        
        add('Metric calculation','metric',QTextEdit(),tip='Used to calculate the quality of the design', val=' + '.join(design.eventNames()[0]))
        
        #moveup: useful for dictionaries, at least until I make a proper widget for it.  don't like the visual of my current Row/Table system for this...
        def contrasts_get(w):
            d=dict()
            txt=w.toPlainText()
            for line in txt.split('\n'):
                line=line.strip()
                if not line:
                    continue
                if line.startswith('#'):
                    continue
                (k,v)=line.split(':')
                k=k.strip()
                v=v.strip()
                d[k]=v
            return d
        def contrasts_set(w,value):
            if not value:
                w.setText('')
            else:
                txt=[]
                for k in value:
                    v=value[k]
                    txt.append('{} : {}'.format(k,v))
                txt='\n'.join(txt)
                w.setText(txt)
        add('Custom contrasts','contrasts',QTextEdit(),tip='Enter custom contrasts here',get=contrasts_get,set=contrasts_set)
        
        layout.addLayout(top)
        layout.addLayout(bot)
        bot.addWidget(self.status)
        bot.addLayout(buts)
        self.setLayout(layout)
        
        # load previous settings
        s = design.optimizationSettings()
        for giz in self.setting_gizmos:
            if giz.var_name in s:
                giz.value = s[giz.var_name]
        
        
        # if already optimized, user may submit
        if design.state == Design.OPTIMIZED:
            self.status.setText('Design previously optimized.')
        elif design.state == Design.TWEAKED:
            self.status.setText('Design previously optimized, with minor changes afterwards.')
        elif design.state == Design.UNOPTIMIZED:
            self.status.setText('Design needs to be optimized.')
        else:
            raise Exception("can't optimize this design...")
        
        #for giz in self.setting_gizmos:
        #    connect(giz,self._onNewSettings)
    

    def _optimize(self,*unused):
        settings = {giz.var_name:giz.value for giz in self.setting_gizmos}
        with self.status_catch as err:
            self.design.optimize(settings)
        if not err:
            self.accept()
        
        
