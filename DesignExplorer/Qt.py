#fixme: this needs tested on more systems
try:
    from PyQt4 import *
    #fixme: why not in __all__!?!?!
    from PyQt4 import QtGui
    from PyQt4 import QtCore
except ImportError:
    from PySide import *
    from PySide import QtUiTools # why not in __all__ ??
    #uic.loadUi('/home/Josh/form1.ui', self)
    # come on people, provide a consistent interface!!!
    # http://qt-project.org/forums/viewthread/43266
    from PySide.QtUiTools import QUiLoader
    class UiLoader(QUiLoader):
        def __init__(self, baseinstance):
            QUiLoader.__init__(self, baseinstance)
            self.baseinstance = baseinstance
        def createWidget(self, class_name, parent=None, name=''):
            if parent is None and self.baseinstance:
                # supposed to create the top-level widget, return the base instance instead
                return self.baseinstance
            else:
                # create a new widget for child widgets
                widget = QUiLoader.createWidget(self, class_name, parent, name)
                if self.baseinstance:
                    # set an attribute for the new child widget on the base
                    # instance, just like PyQt4.uic.loadUi does.
                    setattr(self.baseinstance, name, widget)
                return widget
    class uic(object):
        @classmethod
        def loadUi(cls,uifile, baseinstance=None):
            loader = UiLoader(baseinstance)
            widget = loader.load(uifile)
            QtCore.QMetaObject.connectSlotsByName(widget)
            return widget