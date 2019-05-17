#fixme: should import from Qt.py locally, for compatibility
from PyQt4.QtGui import *
from PyQt4.QtCore import *

        
#clean: looks like perhaps the c++ interface has more conveniences?
# look into SIGNAL and SLOT macros (functions?), maybe I should look
# for python versions of those or model my Widget library like that
# that way, at least the style I use wouldn't be completely novel.
# and it might be better functionally.


#idea: would be nice if there were a chain between 'edited' and 'changed' signals.  could perhaps use a validator?
# the current hook points I know in Qt don't match up well with how I'm wanting to do things...
# or perhaps I'm supposed to be hooking into my own changed signals, and temp blocking signals where needed?
# end result is typically too much repeated code or absurdly modular code...

#clean: this is getting very messy... may be more robust to build a mapping
# for each type directly.  
def set_value(w,val):
    val_is_str = hasattr(val,'capitalize')
    # first convert sequences into comma separated lists
    # this should work as long as there aren't widgets that accept multiple integers, for example.
    if not val_is_str and hasattr(val,'__len__'):
        val=', '.join(map(str,val))
        val_is_str=True
    
    # find the right method to call, thanks qt...
    
    # need issubclass, because things like QTableWidgetItem have setCheckState
    # even thought that's entirely not what I wanted to do ever...  check state
    # in that instance is a state, not a value.
    # and I'm more inclined to think of a button's 'value' as its text, if 
    # anything.
    if isinstance(w,QAbstractButton) and not isinstance(w,QPushButton):
        if hasattr(w,'isTristate') and w.isTristate():
            #idea: any simple way to represent partiallychecked?  Though main
            # goal was for True/False to work so not a huge ommision.
            # None might work, if partially is interpreted as no-change as I've
            # read in at least one place...
            if val not in (Qt.PartiallyChecked, Qt.Checked, Qt.Unchecked):
                if val:
                    val=Qt.Checked
                else:
                    val=Qt.Unchecked
            w.setCheckState(val)
        else:
            w.setChecked(bool(val))
    elif hasattr(w,'setValue'):
        w.setValue(val)
    elif hasattr(w,'setText'):
        w.setText(str(val))
    elif hasattr(w,'setIndex'):
        w.setIndex(int(val))
    elif isinstance(w,QComboBox):
        #fixme: this is a mess.  so many possiblities...  why qt, why?
        if val_is_str:
            i = w.findText(val)
            assert(i!=-1)
            w.setCurrentIndex(i)     
        else:
            w.setCurrentIndex(int(val))
    else:
        raise AttributeError("don't know how to set value for widget {}".format(w))            
    


#opt: wrt Gizmos, would be better to determine the getter/setter up front
#opt: LUT may be better?
def value(w,ty=None):
    if isinstance(w,QAbstractButton) and not isinstance(w,QPushButton):
        ret = w.checkState()
        if ret==Qt.Checked:
            ret=True
        elif ret==Qt.Unchecked:
            ret=False
        else:
            raise NotImplementedError("trying to get value for tristate checkbox like thing, returning 0.5 because I don't really know what to do yet")
            print("WARNING: trying to get value for tristate checkbox like thing, returning 0.5 because I don't really know what to do yet")
            ret=0.5
    else:
        for name in ('value','text','currentText','index','getValue','toPlainText'):
            try:
                ret = getattr(w,name)()
                break
            except:
                pass
        else:
            raise AttributeError("don't know how to get value from widget {}".format(w))    
    
    if ty is not None:
        return ty(ret)
    return ret

def values(w,ty=None):
    ret = value(w)
    try:
        txt=ret
        if ',' in txt:
            ret=txt.split(',')
        elif ' ' in txt:
            ret=txt.split()
        else:
            ret=[txt]
        ret=[r.strip() for r in ret]
    except:
        if not hasattr(ret,'__len__'):
            ret=[ret]
    
    if ty is not None:
        ret=[ty(r) for r in ret]
    return ret




#opt: room for improvement, shouldn't be chained function calls.
_pat='''
def as_{ty}{p}(w):
    return value{p}(w,{ty})
'''
for _p in ('s',''):
    for _ty in 'str float int'.split():
        exec(_pat.format(ty=_ty,p=_p))

    
    
#idea: keep building this.  pretty dumb that there aren't generic signals to connect to,
# hard to write good code when everything has special methods...
def edited_signal(w):
    for name in ('textEdited','valueEdited','stateEdited'): #,'sliderMoved'): #annoy: seems like sliderMoved only works if mouse dragged... seriously?
        if hasattr(w,name):
            return getattr(w,name)
def changed_signal(w):
    for name in ('textChanged','valueChanged','stateChanged'):
        if hasattr(w,name):
            return getattr(w,name)
    a = hasattr(w,'currentIndexChanged')
    b = hasattr(w,'editTextChanged')
    if hasattr(w,'isEditable'):
        e = w.isEditable()
    else:
        e = True
    
    if b and e:
        if a:
            raise NotImplementedError('not sure which to choose, combobox-like widget is editable so both index and text may change...')
        return w.editTextChanged
    if a:
        return w.currentIndexChanged

def signal(w):
    s = edited_signal(w)
    if s:
        return s
    s = changed_signal(w)
    if s:
        return s
    for name in ('clicked',):
        if hasattr(w,name):
            return getattr(w,name)
    
    raise NotImplementedError("couldn't find appropriate signal for {}".format(w))




class signalsBlocked(object):
    '''
    context manager for blocking signals of one or more widgets.  (see blockSignals)
    upon entering, any widgets that that don't already have blocked signals will
    be blocked.  upon exiting, only those signals that were blocked by this context
    manager will be unblocked.
    
    note that if something inside the context block purposefully calls blockSignals(True)
    on one of the widgets intending for this effect to continue past the context block,
    signals will still be unblocked on leaving.  
    
    '''
    def __init__(self,*ws):
        self.ws=ws
    def __enter__(self):
        self.ws = [w for w in self.ws if not w.signalsBlocked()]
        for w in self.ws:
            w.blockSignals(True)
        return self
    def __exit__(self,e_ty,e_val,tb):
        for w in self.ws:
            w.blockSignals(False)
        self.ws=None


class _EventFilter(QObject):
    def __init__(self,fn):
        QObject.__init__(self)
        self._fn = fn
    def eventFilter(self, obj, event):
        return bool(self._fn(obj, event))

class EventFilter(object):
    _refattr = '_event_filter_references'
    def __init__(self,obj,filterer):
        try:
            refs = getattr(obj,self._refattr)
        except AttributeError:
            refs = []
            setattr(obj,self._refattr,refs)
        refs.append(self)
        
        if not isinstance(filterer,QObject):
            filterer = _EventFilter(filterer)
        obj.installEventFilter(filterer)
        
        self._obj = obj
        self._filterer = filterer
        
    def remove(self):
        self._obj.removeEventFilter(self._filterer)
        try:
            refs = getattr(self._obj,self._refattr)
            refs.remove(self)
        except:
            pass

def installEventFilter(obj,filterer):
    return EventFilter(obj,filterer)