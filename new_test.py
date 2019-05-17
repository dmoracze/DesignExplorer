

wdir = '/home/Josh/Dropbox/DesignExplorerRewrite/'

def rrr():
    global mw
    try:
        mw.close()
    except:
        print(str_err())
    
    mw = None
    
    #runfile(__file__, wdir=os.path.dirname(__file__))
    runfile(wdir+'new_test.py', wdir=wdir)
    

#from DesignExplorer import start
#from DesignExplorer.common import *
from DesignExplorer import *
from jkpy import *

# better to use rrr actually, closes things nicer.
try:
    if mw:
        mw.close()
except:
    print(str_err())
    pass

mw = start()

#for i in range(4):
#    mw.activateVisualization(TestVisualization)
mw.window.resize(QSize(752, 472))
#mw.status.resize(QSize(mw.status.width(), 76))
mw.splitter.setSizes([105, 71, 264])
mw.window.resize(QSize(1100,900))
#w0 = mw.visualizations[0].widget
#w1 = mw.visualizations[1].widget

'''
i.d = DockArea()
d.show()
for i in range(4):
    v = TestVisualization(None)
    d.addDockWidget(Qt.BottomDockWidgetArea,v.widget,Qt.Vertical)
'''

'''
def test():
    d = mw._designs[0]
    g = StylesGUI(d)
    g.exec_()
    
test()
'''

'''
m = mw.getMode()
for i in range(5):
    name = 'example{}'.format(i+1)
    if not mw.findDesign(name):
        dout('creating example design {}',i+1)
        d = mw.addDesign(name)
        d.focus()
        m.widget.loadExample(i+1)


''' 
'''
d = mw.designs()[0]
for i in (3,4,5):
    (exp,opts) = d._exportExperiment('blarg{}'.format(i))
    mw.addSS(exp,opts)
'''