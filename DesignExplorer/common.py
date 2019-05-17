from __future__ import absolute_import

'''
This file is mostly a pile of commonly used items that I've been too lazy or otherwise
unable to sort into better named files.  Much of it comes from the previous version of
this project.

Also towards the end, there are imports for most every file in the project.  This is again
a bit lazy, but ensures that the namespace is fully populated as long as you import all
from common.  Quite convenient...

Pretty much every file in this package should start the same way:
    from __future__ import absolute_import
    from .common import *

This will probably the the messiest part of the entire project..

'''

'''
My (Josh's) current understanding of Widgets is that they are a visual representation and manipulator of some stored value.
QCheckBox holds a boolean value, lets the user change the value (click the box) and also
visually displays the current state (checked or unchecked).  Eve for more complicated values, most of the widgets I've desigend
throughout the project follow the same strategy.  They will have a value (which can be get/set) as well as a visual representation
of that value

The end goal is exactly that...  Widgets should only be a holder for some value plus
a graphical interfacefor said value.  Despite all the flaws for Table or Row, I still
think the concept is sound.

But then I'm a bit confused as to why the built in Qt table widgets and such are so
amazingly bad at following this concept There is no obvious way to get a compact set of
values out of a table...  thus why I made Table.
'''


#clean: what is unused?  I just copied this from the old common.py 
# it is very messy in here...

# v2 api is way better, automatically converts to/from q types and python types
# python 3 seems to use version 2 by default, not sure why python 2 does not...
import sip
for _name in ('QDate','QDateTime','QString','QTextStream','QTime','QUrl','QVariant'):
    sip.setapi(_name,2) # the error message is decent, and no error if already 2 or unset.

#fixme: need to wrap this for compatibility
from PyQt4 import QtGui, QtCore
from PyQt4.QtGui import *
from PyQt4.QtCore import *



# ensure a QApplication instance exists
_qapp = None
if not QApplication.instance():
    _qapp = QApplication([])

from . import Widget
from .Widget import signalsBlocked

import re
import os
import sys
import shutil
import subprocess
from glob import glob

from copy import deepcopy
from tempfile import mkdtemp
from tempfile import NamedTemporaryFile as mktemp

from collections import OrderedDict, deque, MutableMapping
from multiprocessing import cpu_count

from jkpy.StimSim import *
from jkpy.StimSim import simulate_internal, InternalExperiment, Part, Parts, Config, setDeconPath
from jkpy import *
from jkpy import pd
from jkpy import sb

# don't trouble users with the logfile additions
# that would come from this program
#idea: perhaps this should be moved to StimSim as well?
os.environ["AFNI_DONT_LOGFILE"] = "YES"

#testing:
DEV_IGNORE_EXISTING = False
DEV_IGNORE_LOAD_ERRORS = True


# overwriting jkpy's perr to use dout instead.  more reliable, more useful
# for this project
def perr(fn):
    '''
    prints exception before reraising it.  Good for async callback methods
    and properties, where the exceptions can get lost or misinterpreted
    '''
    def wrapper(*args,**kwargs):
        try:
            return fn(*args,**kwargs)
        except Exception:
            dout(str_err())
            dout(fn,args,kwargs)
            raise
    return wrapper

class TracingPerr(object):
    '''
    alternative perr implementation that also outputs function enter/exit events.
    replace perr with this if you are getting really lost trying to track down some bug.
    
    Not at all reasonable to use this all the time, too much detail...
    '''
    def __init__(self):
        self.indent = 0
    def __call__(self,fn):
        def wrapper(*args,**kwargs):
            i = '    '*self.indent
            fname = str(fn)
            self.indent += 1
            #fixme: not sure how big a problem it is... but when reloading
            # in spyder (runfile), dout is None.  and the traceback for that
            # is rather unhelpful.  not sure where it is triggered... it
            # could be causing problems with init or close of stuff
            dout(i+"entering "+fname)
            try:
                ret = fn(*args,**kwargs)
            except Exception:                
                dout(i+str_err())                
                self.indent -= 1
                dout(i+"exiting "+fname)
                raise
            else:
                self.indent -= 1
                dout(i+"exiting "+fname)
                return ret
        return wrapper
# use this to enable lots of tracing, not a finished debug system though.
#perr = TracingPerr()

def connect(signal,slot):
    '''
    good for debugging this project.  automatically wraps the slot in perr. all exceptions
    will be printed in the debug console, even if the exceptions are ultimately ignorred.
    '''
    signal.connect(perr(slot))

'''
Still haven't found a good way to handle Qt Widgets/Windows flexibly.  some thoughts/requirements:
    1) child windows need to close when parent windows close
    2) Sometimes want widgets to be widgets, othertimes windows
    3) modality
    4) some dialogs should store state, others should be on-off executions
    5) want convenience for handling user requests (clicking non-modal dialog launcher should raise dialog if it already exists, else make it)
    
Much of the difficulty comes from how I have an interactive console running at the same time.  Qt modal dialogs normally work fine, you
can't close the parent.  But from the console I can easily call close() on the parent and that's where the real annoyance starts.

So honestly, this is more of a development annoyance than an actual problem for eventual users.
'''



class BetterWidget(QWidget):
    '''
    meh... an early attempt at a more convenient base class for widgets?  close events, better resizing, convenience sizing and placement methods...
    would probably remove (or at least rewrite) but it is used in a few other places.  Not a big deal ultimately.
    '''
    closed = pyqtSignal(QCloseEvent)
    @perr
    def closeEvent(self,event):
        self._closeEvent(event)
        self.closed.emit(event)
    #pyqt dumbness, use this rather than closeEvent for derived classes...
    def _closeEvent(self,event):
        pass
    
    def __init__(self,parent = None, flags = None):
        QWidget.__init__(self)
        ##testing:
        #self.setAttribute(Qt.WA_DeleteOnClose)
        if parent or flags:
            self.setParent(parent,flags)
        
        if self.isWindow():
            self.centerGeometry()
    
    def autoSize(self):
        self.resize(self.minimumSizeHint())
    #fixme: doesn't work... seems to think I have only 1 screen!?  why is this not default anyways...
    def centerGeometry(self):
        frameGm = self.frameGeometry()
        screen = QApplication.desktop().screenNumber(QApplication.desktop().cursor().pos())
        centerPoint = QApplication.desktop().screenGeometry(screen).center()
        frameGm.moveCenter(centerPoint)
        self.move(frameGm.topLeft())
    def setTopLevelWindow(self):
        self.raise_()
        self.activateWindow()

Window = BetterWidget

class BetterDialog(QDialog):
    # Like BetterWidget, just for QDialog.  not much here honestly.  early experiment.
    closed = pyqtSignal(QCloseEvent)
    @perr
    def closeEvent(self,event):
        self._closeEvent(event)
        self.closed.emit(event)
    #pyqt dumbness, use this rather than closeEvent for derived classes...
    def _closeEvent(self,event):
        pass #style: or is it better to connect to closed event?
    '''
    def __init__(self, parent, widget=None, app_modal=False, title=None):
        QDialog.__init_(self)
        self.setParent(parent,Qt.Dialog)
        if app_modal:
            self.setWindowModality(Qt.ApplicationModal)
        else:
            self.setWindowModality(Qt.WindowModal)
        if title:
            self.setWindowTitle(title)
        
        if widget is not None:
            lay = QHBoxLayout()
            lay.addWidget(widget)
            self.setLayout(lay)
    '''
    #idea: option to disown widget?
    #fixme: why does this work for the closing chain when my own use of QDialog didn't in PickerButton??
    # is it garbage collection AGAIN?
    def __call__(self, parent, app_modal=False, title=None, widget=None):
        if parent is not None:
            self.setParent(parent, Qt.Dialog)
        if app_modal:
            self.setWindowModality(Qt.ApplicationModal)
        else:
            self.setWindowModality(Qt.WindowModal)
        if title is not None:
            self.setWindowTitle(title)
        if widget is not None:
            lay = QHBoxLayout()
            lay.addWidget(widget)
            self.setLayout(lay)
        
        return self.exec_()
    def __init__(self,*args, **kwargs):
        QDialog.__init__(self,*args,**kwargs)
        ##testing:
        #self.setAttribute(Qt.WA_DeleteOnClose)

# building a more convenient widget.  Not a complete QWidget (or even a subclass at all),
# but very nice for simple things.
#clean: it has a lot of junk from its original use elsewhere...  name shouldn't be first and required.
# w shouldn't default to QLineEdit, etc...
class Gizmo(object):
    '''
    My earlier attempts to build a more convenient QWidget.  Not even a QWidget subclass though...
    
    As with a number of other classes in common.py, I'd remove or rewrite this if only it weren't
    used in many other places!
    
    Plenty of old cruft from initial uses... for example, name shouldn't be the first parameter
    and w shouldn't default to QLineEdit.
    
    After a while, it just adds more confusion.  Better to have inconvenient Qt built-in classes than
    an unfinished Gizmo...
    '''
    def __init__(self, name='', w=None, get=None, set=None, val=None, tip=None, cb=None, wrap=False, **attributes):
        if get is None:
            if val is not None:
                def get(w):
                    return Widget.value(w,type(val))
                get_type=str(type(val))
            else:
                get=Widget.value
                get_type='str'
        else:
            get_type=get.__name__
        
        #idea: can improve this, make more like get handling
        if set is None:
            set = Widget.set_value
        
        if w is None:
            w = QLineEdit() # do you need to specify the parent?
            if val is not None:
                w.setText(str(val))
        else:
            if val is not None:
                Widget.set_value(w,val)
        
        if tip:
            w.setToolTip(tip)
        
        if cb is not None:
            connect(Widget.signal(w),cb)
            #Widget.signal(w).connect(cb)

        if wrap:
            w.setWordWrap(True)
        
        self._get=get
        self._set=set
        self.widget=w
        self.value_type=get_type
        self.name=name
        
        for name in attributes:
            setattr(self,name,attributes[name])
    
    def blockSignals(self,block):
        self.widget.blockSignals(block)
    def signalsBlocked(self):
        return self.widget.signalsBlocked()
    
    @property
    def value(self):
        try:
            return self._get(self.widget)
        except Exception as e:
            backup_e = BetterException(e,"uknown error getting value for {}".format(self.name))
            try:
                ty = type(Widget.value(self.widget))
                raise BetterException(e,"invalid value for {}, Found {} but expected {}".format(self.name,ty,self.value_type))
            except:
                #annoy: this didn't work... traceback was ruined I guess by more recent error?
                #raise BetterException(e,"uknown error getting value for {}".format(self.name))
                raise backup_e
            
    @value.setter
    def value(self,value):
        try:
            self._set(self.widget,value)
        except Exception as e:
            raise BetterException(e, "unable to set {} to have value {}".format(self.name,value))



class PickerWidget(QWidget):
    '''
    My system for creating new widget types that have a held value and a string representation of that value.
    Also a GUI that can be displayed, allowing the user to modify the held value.
    
    see also PickerButton
    '''
    default_value = None
    
    valueChanged = pyqtSignal(object)
    valueEdited = pyqtSignal(object)
    
    submitted = pyqtSignal()
    canceled = pyqtSignal()
    
    def __init__(self,*args,**kwargs):
        QWidget.__init__(self,*args,**kwargs)
        self._gizmos=OrderedDict()
        self._value = None
        self._txt = None
        self._opt_config = None
        appendStyleSheet(self, '''
            .QWidget {
                border: 0px;
            }
            .QPushButton {
                background-color: #cccccc;
                font: normal 12px;
                border-style: outset;
                border-width: 1px;
                border-radius: 2px;
                border-color: black;
                width: 50px;
                height: 10px;
                padding: 4px;
                margin: 4px
            }
            .QPushButton:pressed {
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #999999, stop:1 #a6a6a6)
            }
            .QLineEdit {
                border: 1px solid #666666;
                background-color: #ffffff;
                max-width: 150px;
            }
            .QSpinBox {
                background-color: #ffffff;
                max-width: 150px;
            }
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
                min-width: 150px;
            }
            .QAbstractItemView {
                background-color: #ffffff;
                selection-color: #000000;
            }
        ''')

    
    def __str__(self):
        return self._txt
    __repr__ = __str__ #fixme: can have better repr, or is that not important anymore?
    
    # given a value, modify it to be valid then return it.
    def _validateValue(self,value):
        return value
    
    # given a valid value, represent it as a string
    def _reprValue(self,value):
        return str(value)
    
    # given a configuration, return a value
    def _parseConfig(self, opt, config):
        pass
    
    # given a valid value, generate a configuration (to update the form). (opt,config) format
    def _makeConfig(self, value):
        pass
    
    
    def text(self):
        return self._txt
    #idea: load from text (setText)
    
    def value(self):
        return self._value
    def setValue(self,value):
        value = self._validateValue(value)
        self._txt = self._reprValue(value)
        self._value = value
        (opt,config) = self._opt_config = self._makeConfig(value)
        #why wasn't this here??
        self.config(opt,**config)
        self.valueChanged.emit(self._value)
    
    def add(self,opt):
        self._gizmos[opt]=dst=[]
        class OptContext:
            def __enter__(this):
                return this
            def __exit__(this,*args):                
                pass
            
            def __call__(this,*args,**kwargs):
                store = kwargs.pop('store',True)
                giz=Gizmo(*args,**kwargs)
                giz.store = store
                dst.append(giz)
        return OptContext()
    @perr
    def build_layout(self):
        
        layouts = QStackedLayout(self)
        layouts.setSpacing(10)
        for opt in self._gizmos:
            gizmos=self._gizmos[opt]
            
            form_layout=QFormLayout()
            form_layout.setSpacing(10)
            for giz in gizmos:
                form_layout.addRow(giz.name,giz.widget)
            
            form_widget=QWidget()
            form_widget.setLayout(form_layout)
            layouts.addWidget(form_widget)
        self._layouts=layouts
        
        dw=QComboBox(self)
        dw.setStyle(QtGui.QStyleFactory.create('Cleanlooks'))
        self._opt_widget=dw
        for opt in self._gizmos:
            dw.addItem(opt)
        connect(dw.activated,self._on_opt_change)
        
        layout = QVBoxLayout()
        cmb_lay = QHBoxLayout()
        cmb_lay.addStretch()
        cmb_lay.addWidget(dw)
        cmb_lay.addStretch()
        layout.addLayout(cmb_lay)
        
        forms_widget=QWidget()
        forms_widget.setLayout(layouts)
        form_lay = QHBoxLayout()
        form_lay.addWidget(forms_widget)
        form_lay.addStretch()
        layout.addLayout(form_lay)

        bb=QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        connect(bb.button(QDialogButtonBox.Ok).clicked,self._submit)
        connect(bb.button(QDialogButtonBox.Cancel).clicked,self._cancel)
        layout.addWidget(bb)
        
        self.status_widget = QLabel()
        layout.addWidget(self.status_widget)
        
        self.setLayout(layout)
        
        self.setValue(self.default_value)

        return layout
    
    def setStatus(self,txt):
        self.status_widget.setText(txt)
    
    def config(self,opt,**settings):
        i=self._opt_widget.findText(opt)
        if i==-1:
            raise KeyError('option {} is not valid'.format(opt))
        self._opt_widget.setCurrentIndex(i)
        self._on_opt_change() # huh...
        
        parts=self._gizmos[opt]
        #print('config',parts,settings)
        for part in parts:
            #print('pre',part.name,part.value)
            #print(part.name)
            if part.name in settings:
                #print('setting',part.name,settings[part.name])
                #print(settings[part.name])
                part.value = settings[part.name]
            #print('post',part.name,part.value)
            
    def _on_opt_change(self,*args):
        self._layouts.setCurrentIndex(self._opt_widget.currentIndex())
        
    def _submit(self,*args):
        opt=self._opt_widget.currentText()
        parts=self._gizmos[opt]
        data = [(g.name,g.value) for g in parts if g.store]
        config = OrderedDict(data)
        #config=dict(data)
        try:            
            value = self._parseConfig(opt,config)
        except Exception:
            err='{}: {}\n\n{}'.format(opt,config,str_err())
            self.setStatus(err)
            return
        
        value = self._validateValue(value)
        self._txt = self._reprValue(value)
        self._opt_config = (opt,config)
        
        if self._value != value: #is this worth doing? doesn't quite fit with valueEdited terminology... but isn't it always what is intended?
            self._value = value
            self.valueEdited.emit(self._value)
            self.valueChanged.emit(self._value)
            self.submitted.emit()
    
    def _cancel(self,*args):
        if self._opt_config:
            (opt,config) = self._opt_config
            self.config(opt,**config)
            self.setStatus('')
        
        self.canceled.emit()

#opt: was too much of a mess to try and make the widget on-demand... but it should be possible
# if absolutely necessary.
class PickerButton(QPushButton):
    '''
    see also PickerWidget
    
    clicking the button launches the associated picker widget.  button text always matches
    the picker widget (can even setText and the picker widget value is changed.)
    '''
    valueEdited = pyqtSignal(object)
    valueChanged = pyqtSignal(object)
    
    def __init__(self, widget, txt_format='{}', parent=None):
        QPushButton.__init__(self, parent)
        appendStyleSheet(self,'''
            QPushButton{
                background-color: #f2f2f2;
                max-height:15px;
                border-radius: 0px;
                border: 1px solid #000000;
                margin-top: 5px;
                margin-bottom: 5px;
                margin-left: 5px;
                margin-right: 5px;
                padding-top: 2px;
                padding-bottom: 2px;
                padding-left: 10px;
                padding-right: 10px;
            }
            QPushButton:pressed {
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #999999, stop:1 #a6a6a6)
            }
        ''')
        self._widget = widget
        self._txt_format = txt_format
        self._update()
        connect(self.clicked,self._show)
        
        connect(self._widget.submitted,self._accept)
        connect(self._widget.canceled,self._reject)
        
        #self.destroyed.connect(self._destroyedEvent)
        
        #testing:
        #self.setAttribute(Qt.WA_DeleteOnClose)
        #self.setAttribute(Qt.WA_QuitOnClose)
        
        #parent.closed.connect(self.closeEvent)
    
    #annoy: not sure why this isn't called?!?!??
    '''
    @perr
    def setParent(self,parent,flags=None):
        print('setParent',parent)
        prev = self.parent()
        if prev is not None:
            prev.closed.disconnect(self.closeEvent)
        parent.closed.connect(self.closeEvent)
        
        if flags is None:
            QPushButton.setParent(parent)
        else:
            QPushButton.setParent(parent,flags)
    '''
    @perr
    def closeEvent(self,event):
        if self._dia is not None:
            self._dia.close()
            self._dia = None
    @perr
    def _destroyedEvent(self,*args,**kwargs):
        #print('destroyed',self)
        if self._dia is not None:
            self._dia.destroy()
            self._dia = None
    @perr
    def _accept(self):
        self._dia.accept()
    @perr
    def _reject(self):
        self._dia.reject()
        
    @perr
    def _show(self,event):
        #print('pwb parent',self.parent())
        w = self._widget
        
        self._dia = dia = BetterDialog()
        self._dia.setWindowOpacity(1)
        if dia(self,widget = w):
            self._value = w.value()
            self._txt = self._txt_format.format(w.text())
            
            self.setText(self._txt)
            self.valueEdited.emit(self._value)
            self.valueChanged.emit(self._value)
        
        w.setParent(None)
        #lay.removeWidget(w)
        self._dia = None
    
    def value(self):
        return self._value
    def setValue(self,value):
        self._widget.setValue(value)
        self._update()
        self.valueChanged.emit(self._value)
    
    def _update(self):
        w = self._widget
        self._value = w.value()
        self._txt = self._txt_format.format(w.text())
                
        self.setText(self._txt)

class StatusCatch(object):
    '''
    A context manager for transforming exceptions into status messages.
    When in this context, setStatus(pre+err) will be displayed if
    an Exception is caught.  pre is set when entering the context (defaults
    to '').  err will be the exception text, optionally the traceback too.
    
    A good way to automatically translate exceptions into user-focused error messages,
    as long as your original exceptions are implemented such that the messages are
    useful.
    '''
    def __init__(self,setStatus=None, show_traceback=False):
        self.failed=False
        self.setStatus = setStatus
        self.pre_message=''
        self.show_traceback=show_traceback
        self._status = ''
    def __enter__(self):
        self.failed=False
        return self
    def __call__(self,pre_message='',*args,**kwargs):
        if args or kwargs:
            pre_message=pre_message.format(*args,**kwargs)
        self.pre_message=pre_message
        return self
    def __exit__(self,e_ty,e_val,tb):
        pre=self.pre_message
        if pre:
            pre+='\n'
        self.pre_message=''
        ret=True
        
        if e_ty is not None:
            self.failed=True
            
            if e_ty==AssertionError:
                ret=False
                msg=str_err(e_ty,e_val,tb)
            else:
                if self.show_traceback:
                    msg=str_err(e_ty,e_val,tb)
                else:
                    msg=str_err(e_ty,e_val)
                #testing:
                dout(str_err(e_ty,e_val,tb))
            self._status = pre+msg
        else:
            self._status = ''
        
        if self.setStatus is not None:
            self.setStatus(self._status)
        return ret
    
    def __str__(self):
        return self._status
    
    
    def __bool__(self):
        return self.failed
    __nonzero__=__bool__


class QLabeledSlider(QSlider):
    '''
    a QSlider that also has a label.  I wish most QWidgets had such an option...
    
    really just an early experiment.  If this were to be more broadly useful,
    would require more work.
    
    Somewhere else I have an expanded version of this?  labeled widgets...  first
    argument is a label, all subsequent arguments are widgets to be placed after the label.
    Implementationally it is just a QHBoxLayout.  Eventually, this class should be phased out
    in prefrerence for the alternative.
    '''
    def __init__(self,*args,**kwargs):
        QSlider.__init__(self,*args,**kwargs)
        connect(self.valueChanged,self._updateLabels)
        self._label = QLabel()
        self._label.setText('0')
        self.setFocusPolicy(Qt.ClickFocus)
        #lay = QHBoxLayout()
        #lay.addWidget(self)
        #lay.addWidget(self._label)
        #self.setLayout(lay)
        
    def _updateLabels(self,value):
        self._label.setText(str(value))
    @perr
    def paintEvent(self,event):
        QSlider.paintEvent(self,event)
        p = QPainter(self)
        rect = self.geometry()
        x=rect.width()/2.0
        y=rect.height()
        p.setPen(QPen(Qt.red))
        p.drawText(QPoint(0,y),str(self.value()))



def screenShow(w,N=2,full=False):
    '''
    shows the given widget on a specified monitor (default 2 for some reason)
    optionally full screened.  just development convenience.
    '''
    res = QApplication.desktop().screenGeometry(N)
    w.move(QPoint(res.x(),res.y()))
    if full:
        w.resize(res.width(),res.height())
        w.showFullScreen()
    else:
        w.show()

def convenientStringFormatting(msg,*args,**kwargs):
    '''
    msg.format(*args,**kwargs)
    else str((msg,)+args)
    
    I've found it pretty convenient.  dout uses this!    
    '''
    # 
    tuple_mode = False
    if args or kwargs:
        tuple_mode = True
        try:
            formatted_msg = msg.format(*args,**kwargs)
            #fixme: there are some courner cases in which this fails.
            # would be better to use string.Formatter, probably a derivation of it
            # to detect if formatting is required at all.
            if msg != formatted_msg:
                tuple_mode = False
                msg = formatted_msg
        except:
            pass
    if tuple_mode:
        assert(not kwargs)
        msg = str((msg,)+args)
    else:
        msg = str(msg)
    return msg

def appendStyleSheet(w,s):
    '''
    append to an existing stylesheet rather than ignorantly overwriting whatever is already there.
    
    But this isn't a perfect solution...  You really should consider potential conflicts.  And if you
    plan to change things later don't use hardcoded styles.  instead create a dynamic property and be sure
    to ensurePolished and polish upon changes.
    '''
    w.setStyleSheet(w.styleSheet()+'\n'+s)

class DebugConsole(object):
    '''
    just for development (currently).  A Borg style class.  plain text edit
    widget using convenientStringFormatting.  used throughout the project
    to display tracebacks and debug print statements.
    '''
    w = None
            
    def __init__(self):
        if not self.w:
            DebugConsole.w = QPlainTextEdit()
            self.show()
    def __call__(self,msg,*args,**kwargs):
        if not self.w.isVisible():
            return
        msg = convenientStringFormatting(msg,*args,**kwargs)
        self.w.appendPlainText(msg)
        self.w.verticalScrollBar().setValue(self.w.verticalScrollBar().maximum())
    
    def close(self):
        self.w.close()
    def hide(self):
        self.w.hide()
    def show(self):
        screenShow(self.w,1,full=False)
        self.w.raise_()
        self.w.activateWindow()
    
    def __del__(self):
        self.close()

dout = DebugConsole()


class LockFile(object):
    '''
    given a file path, will attempt to create that file and lock it such that
    any other attempts to do the same will fail.  Good for cooperatively claiming
    project folders.  Main won't be given control over a project folder if
    another Main instance somewhere has already locked that folder.
    '''
    '''
    import time
    fpath = '/home/Josh/lock.lock'
    while True:
        lock = LockFile(fpath)
        if lock._locked:
            break
        print('waiting')
        time.sleep(1)
    print('acquired')
    '''
    def __init__(self,fpath):
        self._fpath = fpath
        self._locked = False
        self._win = sys.platform=='win32'
        self.lock()
    
    @property
    def locked(self):
        return self._locked
    @property
    def path(self):
        return self._fpath
    
    def lock(self):
        if self._locked:
            return True
        fpath = self._fpath
        if self._win:
            try:
                # is this check necessary?
                if os.path.exists(fpath):
                    os.unlink(fpath)
                
                self._h = os.open(fpath, os.O_CREAT | os.O_RDWR | os.O_EXCL)
            except OSError as e:
                if e.errno==13:
                    return False
                raise
        else:
            import fcntl
            # it seems like this statement cannot fail unless fpath is invalid
            # if it works, there is no exclusivity yet?
            # but what about permissions?  If root locks and then app crashes,
            # then what??  or if multiple users?
            self._h = open(fpath,'w')
            
            try:
                fcntl.lockf(self._h, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except IOError:
                # supposedly not necessary, but doesn't seem to hurt?
                self._h.close()
                return False
        self._locked = True
        return True
    def unlock(self):
        # seems to be optional, the fcntl stuff
        # is released just fine?  even when locking process got SIGKILLed        
        if not self._locked:
            return True
        h = self._h
        fpath = self._fpath
        
        if self._win:
            os.close(h)
            os.unlink(fpath)
        else:
            import fcntl
            fcntl.lockf(h,fcntl.LOCK_UN)
            
            # does not seem to be needed, nor does it hurt?
            h.close()
            try:
                os.unlink(fpath) # can this fail?  I saw an if statement in an example, seems like a race condition...
            except:
                pass
        
        self._locked = False
        return True
    
    def __del__(self):
        self.unlock()


#clean: I don't like this approach, but it works better than having everything
# in one huge file.  So eventually need to split up this common.py
from .DataFrameWidget import DataFrameWidget
from .MPL import *
from .Tables import *
from .Docking import *
from .Optimization import *
from .Bases import *
from .unsorted import *
from .Main import Main
