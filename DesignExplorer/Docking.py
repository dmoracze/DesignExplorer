from __future__ import absolute_import
from .common import *

'''
Despite what you might expect, Qt doesn't provide implementations for seemingly 
basic features.  So this file is dedicated to reasonably useful dockable windows.
'''



class CustomDockWidgetToolBar(QToolBar):
    '''
    for use with DockWidget.
    
    originally based on Enki code, but I've changed a lot.  no longer
    particularly generic.  Enki may still be a good source for working examples.
    see http://nullege.com/codes/show/src@e@n@enki-HEAD@enki@widgets@dockwidget.py/143/PyQt4.QtGui.QDockWidget.setTitleBarWidget
    
    Far from generic...  it works for what I need it do do currently, but is entirely
    unacceptable for broader applications.
    '''
    # 
    def setTitle(self,title):
        self._title.setText(title)
    def __init__(self, parent, *args):
        QToolBar.__init__(self, parent, *args)        
        # I don't need it really, but a toolbar class should support an icon
        
        self.setSizePolicy( QSizePolicy( QSizePolicy.Expanding, QSizePolicy.Maximum ) )
        self._dock = parent
                
        self._title = QLabel(self)
        self._title.setSizePolicy( QSizePolicy( QSizePolicy.Expanding, QSizePolicy.MinimumExpanding ) )
        self._title.setText(self._dock.windowTitle())
        self._title.setIndent(4)
        self.insertWidget(None,self._title)
        
        self.aClose = QToolBar.addAction(self, self.style().standardIcon( QStyle.SP_TitleBarCloseButton ), "")
        connect(self.aClose.triggered,lambda *args,**kwargs: self._dock.close())
        
        self.setMovable( False )
        self.setFloatable( False )
        
        textHeight = QFontMetrics(self.font()).height()
        self.setIconSize(QSize(textHeight, textHeight))
        appendStyleSheet(self,'''
            background-color: #e6e6e6;
        ''')
    
    def minimumSizeHint(self):
        return QToolBar.sizeHint(self)
    
    def sizeHint(self):
        wis = self.iconSize()
        size = QToolBar.sizeHint(self)
        fm = QFontMetrics ( self.font() )
  
        if  self._dock.features() & QDockWidget.DockWidgetVerticalTitleBar :
            size.setHeight(size.height() + fm.width( self._dock.windowTitle() ) + wis.width())
        else:
            size.setWidth(size.width() + fm.width( self._dock.windowTitle() ) + wis.width())
        
        return size
    
    #impl: don't like this interface much (incomplete).  but I don't know
    # what I'll need (if anything) yet so may as well wait before making
    # changes here.
    # at the moment, the only addition I'm considering is a settings button
    # for changing Visualization specific settings.
    def addAction(self, action):
        """QToolBar.addAction implementation
        Adjusts indexes for behaving like standard empty QTitleBar
        """
        return self.insertAction(self.aClose, action)
  
    def addSeparator(self):
        """QToolBar.addAction implementation
        Adjusts indexes for behaving like standard empty QTitleBar
        """
        return self.insertSeparator(self.aClose)
  
    def addWidget(self, widget):
        """QToolBar.addAction implementation
        Adjusts indexes for behaving like standard empty QTitleBar
        """
        return self.insertWidget(self.aClose, widget)

class DockWidget(QDockWidget):
    '''
    Do not set size constraints on the dock widget itself (it is internally managed by QDockWidget
    and the QMainWindow holding it to accomodate the contained widget).  Not my 
    fault, this is just how Qt does things.  
    
    
    Interested in tracking dock movements?  Go read through unsorted.py.  It is a huge
    mess.  It isn't up to you, you have to worry about what events parent and children widgets might be
    intercepting.  All attempts to hook into dock movement events have failed miserably.
    
    Eventually I did see some promise in using a global even filter.  Indeed, it appears 
    necessary to inspect every single event in the entire application just to detect simple
    events relevent to a dockable window...
    '''
    
    closed = pyqtSignal()
    shown = pyqtSignal()
    
    def __init__(self, name=''):
        QDockWidget.__init__(self)
        self._title_bar = tb = CustomDockWidgetToolBar(self)
        self.setTitleBarWidget(tb)
        self.setObjectName(str(self.__class__))
        self.setTitle(name)
        self.potentially_moving = False
        #appendStyleSheet(self,"""
        #border: 1px solid red;
        #""")
        
        #self.setFeatures(QDockWidget.DockWidgetClosable | QDockWidget.DockWidgetMovable)
    
    def closeEvent(self, event):
        self.closed.emit()
    def showEvent(self, event):
        self.shown.emit()
    
    def setTitle(self,title):
        self._title_bar.setTitle(title)
        QDockWidget.setWindowTitle(self,title)
    def setWindowTitle(self,title):
        self.setTitle(title)
    def title(self):
        return self.windowTitle()


class DockArea(QMainWindow):
    '''
    For some reason, QMainWindow is the only class that handles QDockWidgets
    And QMainWindow can be used as a child widget, "intuitively" doesn't need to
    be a main window at all!  So this class is provided to not just sidestep the poor
    naming (QMainWindow suggests that the widget has to be a single main window...) but
    also to fix some sizing issues.
    
    see minimumSizeHint for details, or just ignore it (as I would have preferred to 
    do, had Qt not been so disappointing...)
    '''
    _separator_size = 5
    def __init__(self,parent=None):
        QMainWindow.__init__(self,parent)
        # I've read that it is required to have a central widget (even if unused)
        self.setCentralWidget(QWidget())
        self.centralWidget().hide()
        
        #self.setDockOptions(QMainWindow.AllowNestedDocks|QMainWindow.AnimatedDocks|QMainWindow.AllowTabbedDocks)
        #self.setDockOptions(QMainWindow.AllowNestedDocks|QMainWindow.AnimatedDocks)
        #self.setDockOptions(QMainWindow.AllowNestedDocks|QMainWindow.AnimatedDocks|QMainWindow.AllowTabbedDocks)
        self.setDockOptions(QMainWindow.AllowNestedDocks|QMainWindow.AnimatedDocks)
        #self.setDockOptions(QtGui.QMainWindow.AllowNestedDocks|QtGui.QMainWindow.AnimatedDocks)
        #self.setTabPosition(Qt.AllDockWidgetAreas, QTabWidget.North)
        #self.setTabPosition(Qt.AllDockWidgetAreas, QTabWidget.West)
        #self.setTabPosition(Qt.AllDockWidgetAreas, QTabWidget.South)
        
        #self.setSizePolicy( QSizePolicy( QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding ) )
        
        #annoy: surely there is a way to read the properties that are set via style sheets?
        # else how does anything work layoutwise inside Qt??
        appendStyleSheet(self,"""
        QMainWindow::separator {{
            background-color: red;
            height: {}px;
        }}
        """.format(DockArea._separator_size))
        
        #self.setSizePolicy( QSizePolicy( QSizePolicy.Maximum, QSizePolicy.Maximum ) )
    
    #idea: I don't fully understand the area argument yet.  when the dock space
    # becomes complex and nested, is there a way to add something fully
    # to one side of everything?  I don't think that this simple
    # approach here does that...
    def addDockWidget(self, area, widget, orientation=None):
        if orientation is None:
            orientation = Qt.Vertical
        
        QMainWindow.addDockWidget(self, area,widget,orientation)
    
    
    '''
    Qt disallows dropping a QDockWidget when there is insufficient room currently available
    to accomadate the new widget.  Without any exception raised or visual feedback...  it'll just
    refuse to let you drop a dock widget into a dock area if it doesn't currently have enough space.
    Even if wrapped in a scroll area... Qt doesn't care.
    
    I spent two or so days trying to figure this nonsense out.
    
    The solution is to reimplement minimumSizeHint (And sizeHint) such that there is always
    enough room.  Again, seems brain-dead-obvious that minimumSizeHint should hint at the minimum
    size for a widget to function properly?  Yet supposedly this isn't a bug?
    
    And so I reimplement minimumSizeHint to account for the worst-case potential move.  find
    the largest docked widget and ensure it can be moved to any location.
    
    Annoying but effective.  I'd rather not require these scroll areas show up, but
    this is so much better than having the dock area "mysteriously" refuse to accept
    new docks...
    '''
    def sizeHint(self):
        return self.minimumSizeHint()
    def minimumSizeHint(self):
        small = QMainWindow.minimumSizeHint(self)
        wmax=0
        hmax=0
        for c in self.findChildren(QDockWidget):
            s = c.minimumSize()
            if s.width() > wmax:
                wmax = s.width()
            if s.height() > hmax:
                hmax = s.height()
        incoming = QSize(wmax,hmax)
        
        margin = self.contentsMargins()
        ss = DockArea._separator_size
        other = QSize(ss+margin.left()+margin.right()+1, ss+margin.top()+margin.bottom()+1)
        
        return small + incoming + other