
#idea: this is close but... it needs to match the pyqtSignal class better
# and also use weakref I believe.  very convenient, probably essential
# for sanity, to make disconnect be optional.  
class Signal(object):
    '''
    http://blog.abstractfactory.io/dynamic-signals-in-pyqt/
    '''
    def __init__(self):
        self.__subscribers = []
        self.signal = 'GenericSignal'
    def emit(self, *args, **kwargs):
        for subs in self.__subscribers:
            subs(*args, **kwargs)
    def connect(self, func):
        self.__subscribers.append(func)        
    def disconnect(self, func=None):
        if func is None:
            self.__subscribers = []
        
        try:  
            self.__subscribers.remove(func)  
        except ValueError:  
            
            print('Warning: function %s not removed '
                  'from signal %s'%(func,self))



####################################################################################################################
## A mess of attempts trying to get scroll-on-drag for a scrollarea.
'''
OK.  so I can get all events filtered by using the application instance.
performance seems fine.

I think it should work if the scroll area doesn't modify any of the events?
Though some implementations that I've seen accept the events during the scroll
rather than letting them through...  may be worth a try still.  

    and in practice, I don't care if the scroll area does eat the events.

will require a good bit of geometry testing.

simplest approach could just be to have scroll edges and scroll that way
if a drag operation is detected.


'''

'''
class EventFilterHandler(QObject):
    def __init__(self,handler):
        QObject.__init__(self)
        self._handler = handler
    def eventFilter(self,*args,**kwargs):
        return self._handler(*args,**kwargs)
def connectEventFilter(src,fn):
    handler = EventFilterHandler(fn)
    src.installEventFilter(handler)
'''



class DragAwareScrollArea(QScrollArea):
    def __init__(self,parent=None):
        QScrollArea.__init__(self,parent)
        
        #self._mouse_pos = QPoint()
        #self._scroll_pos = QPoint()
        
        #self.connect()
        #self.installEventFilter(self)
        self.viewport().installEventFilter(self)
        
    '''
    def mousePressEvent(self,event):
        self._mouse_pos = QPoint(event.pos())
        self._scroll_pos.setX(self.horizontalScrollBar().value())
        self._scroll_pos.setY(self.verticalScrollBar().value())
        #event.accept()
    def mouseMoveEvent(self,event):
        if self._mouse_pos.isNull():
            #event.ignore()
            return
        
        self.horizontalScrollBar().setValue(self._scroll_pos.x() - event.pos().x() + self._mouse_pos.x())
        self.verticalScrollBar().setValue(self._scroll_pos.y() - event.pos().y() + self._mouse_pos.y())
        self.horizontalScrollBar().update()
        self.verticalScrollBar().update()
        #event.accept()
  
    def mouseReleaseEvent(self, event):
        self.mousePressPos = QPoint()
        #event.accept()
    '''
    '''
    @perr
    def dragLeaveEvent(self,event):
        raise Exception('hwy')
        print(event.pos())
        print(event)
        print(self.geometry())
        # but should I ignore non-dock drags?
    '''
    '''
    @perr
    def eventFilter(self,obj,event):
        # I think that 'viewportDragMoveEvent' is just due to the viewport.
        # so I should be able to just do nothing with the event.
        # wait, I do have a viewport...  confusing!!
        etype = event.type()
        #tomain(event=event)
        
        #do I have to disable this when dying?
        if etype == QEvent.DragMove:
            raise Exception('come on')
            scolor('red')
            #impl: check if at the edges.  if so, start scrolling
            # the example code then accepted the event
            # if not scrolling, then forward the event to viewport
            vp = event.pos()
            m = self._scroll_margin
            vw = self.viewport().width()
            vh = self.viewport().height()            
            inside_margin = QRect(m,m,vw-2*m, vh-2*m)
            if not inside_margin.contains(vp):
                self._startDragAutoScroll()
                event.accept(QRect(0,0,0,0))
            else:
                pass
                #forward?
        elif etype in (QEvent.DragLeave, QEvent.Drop):
            raise Exception('leave')
            scolor('blue')
            #impl: stop auto scrolling
            # example fowarded this to the viewport?
            self._stopDragAutoScroll()
            #impl: forward event?
        
        #finally, let base class handle its stuff
        return QScrollArea.eventFilter(self,obj,event)
    
    def _startDragAutoScroll(self):
        #scolor('red')
        pass
    def _stopDragAutoScroll(self):
        #scolor('blue')
        pass
    '''
    '''
    def mousePressEvent(self,event):
        if event.button() == Qt.LeftButton:
            print('click down')
    def mouseReleaseEvent(self,event):
        if event.button() == Qt.LeftButton:
            print('click up')
    '''
    
    @perr
    def eventFilter(self,obj,event):
        et = event.type()
        if et==QEvent.Wheel:
            event.ignore()
        elif et == QEvent.DragMove:
            event.ignore()
        elif et == QEvent.MouseMove:
            event.ignore()
        elif et == QEvent.MouseButtonPress:
            if event.button()==Qt.LeftButton:
                event.ignore()
        elif et == QEvent.MouseButtonRelease:
            if event.button()==Qt.LeftButton:
                event.ignore()
        else:
            pass
        
        return False
#idea: 
def eventName(event):
    if isinstance(event,QEvent):
        val = event.type()
    elif isinstance(Event,QtCore.Type):
        pass
        



class GlobalEventFilter(QObject):
    def eventFilter(self,obj,event):
        et = event.type()
        '''
        if et==QEvent.Wheel:
            event.ignore()
        elif et == QEvent.DragMove:
            event.ignore()
        elif et == QEvent.MouseMove:
            event.ignore()
        elif et == QEvent.MouseButtonPress:
            if event.button()==Qt.LeftButton:
                event.ignore()
        elif et == QEvent.MouseButtonRelease:
            if event.button()==Qt.LeftButton:
                event.ignore()
        else:
            pass
        '''
        if et==QEvent.DragMove:
            '''
            #impl: check if at the edges.  if so, start scrolling
            # the example code then accepted the event
            # if not scrolling, then forward the event to viewport
            vp = event.pos()
            m = self._scroll_margin
            vw = self.viewport().width()
            vh = self.viewport().height()            
            inside_margin = QRect(m,m,vw-2*m, vh-2*m)
            if not inside_margin.contains(vp):
                self._startDragAutoScroll()
                event.accept(QRect(0,0,0,0))
            else:
                pass
                #forward?
            '''
        elif et in (QEvent.DragLeave, QEvent.Drop):
            #impl: stop auto scrolling
            # example fowarded this to the viewport?
            #self._stopDragAutoScroll()
            #impl: forward event?
        return False

qapp = QApplication.instance()
try:
    qapp.removeEventFilter(globalEventFilter)
except:
    pass
globalEventFilter = GlobalEventFilter()
qapp.installEventFilter(globalEventFilter)


##########################################################################################
##  Thoughts regarding Windows, and afni dependencies in general
'''
StimSim only really needs to use 3dDeconvolve.  There is one usage of the mv
command but that can be done in Python.
    trying to compile 3dDeconvolve on Windows seems like a terrible idea
    
    should test if 3dDeconvolve can work standalone.  Its source code certainly
    has many dependencies, but perhaps the binary is fine.  not sure if it is
    downloadable standalone though.  may have to ask for permission to rebundle
    it?
    
    maybe there are alternatives to 3dDeconvolve?
    
    at a certain point, why don't users just have afni?  isn't it useful??

    could try to do just the decon and optimization iterations remotely, but
    not sure how worthwhile such a feature is.
'''






#################################################################################################################
    '''
    *sigh* StimSim.InternalExperiment is a bit of a mess...  Here are my notes
    
    easiest solution is to have Design mark InternalExperiment as dirty whenever
    the temp folder changes.  
    
    I do not like how StimSim relies on having actual files present.  This will be fixed
    eventually, but for now it must be accounted for.
    
    _make_stimes takes a prefix, result is:
        _stim_path_list
        num_stims (same)
        _event_names (same)
        _stim_paths (NEW)
    
    _build_3dD assumes valid
        _stim_paths
    
    _deconvolve
    _just_x1D
        result is to make an x1D file in the specified folder
    _just_metric
        I think it is safe, calls _deconvolve using a temp folder,
        sets the quality attribute then deletes the temp folder.
    
    generate
        _make_stimes using the instance's prefix, thus triggering whatever
        _make_stimes does
        
        also saves _path_res, return value of _deconvolve (uses foler attribute too)
    
    evaluate
        if already evauated, uses current results
        if not generated, first calls generate
        
        uses _path_res to evaulate quality
        
        definitely uses _stim_paths, even loads them, can assume that any quality values are
        dependent on this.
    
    
    nothing else has a direct dependency on disk.
    
    
    not too expensive to do a full generate/evaulate on loading.  So if I trust the
    random seed to be a safe value to archive, it would be sufficient to always
    generate/evalute an InternalExperiment upon loading.
        Eventually I'll rewrite StimSim to make this better.  no disk dependency,
        no reliance on seeds (except as a potential optimization for quick save/load
        usage).
    
    set_dirty = _reconfig
        given no extra settings (no actual reconfiguration), effective result
        is that the InternalExperiment will build+generate+evaluate again as
        needed (eprop)
        
        as long as _build is stable given its seed, this is fine.
        
        generate is not well designed given current usage.  Basically a pre-evalutate
        
        evalute just calculates the results, quality metrics and such.
        
        
        
    
        
    
    3dDeconvolve stuff uses preset path for referencing the stimes files
    
    
    if eventlists are ever supported there are more things to consider
    
    '''
    
###########################################################################################
    
#moveup: needs a name...
class SS(object):
    '''
    a context manager for temporarially changing mapping/attribute values
    '''
    def __init__(self, base, what, value, key=False):
        self.base=base
        self.value=value
        self.what=what
        self.key=key
    def __enter__(self):
        if self.key:
            self.prev=self.base[self.what]
            self.base[self.what]=self.value
        else:
            self.prev=getattr(self.base,self.what)
            setattr(self.base,self.what,self.value)
        return self
    def __exit__(self, *args):
        if self.key:
            self.base[self.what]=self.prev
        else:
            setattr(self.base,self.what,self.prev)

#clean: a mess of bad code, but it works...
def parse_numpy_random():
    '''
    parses numpy.random to collect various details about random distributions
    available in numpy for use by RandomDistributionWidget(PickerWidget)
    
    Not actually used!  but it was interesting enough that I've not yet moved
    or deleted it.  Seems like it could be useful, just not for DesignExplorer.
    '''
    x=dict()
    for n in dir(np.random):
        try:
            f = getattr(np.random,n)
            d = f.__doc__.strip().split('\n')
            sig = d[0]
            args = sig.replace(n+'(','').replace(', size=None','').replace(')','').split(', ')
            argnames=[]
            argvals=[]
            for arg in args:
                if '=' in arg:
                    (name,val)=arg.split('=')
                    val=float(val)
                else:
                    name=arg
                    val=0
                argnames.append(name)
                argvals.append(val)
            desc = d[2].strip()
            if 'distribution' in desc:
                class RandomDistribution(object):
                    def __init__(self,*args,**kwargs):
                        # if args are used, convert them into kwargs
                        if args or True: #testing: do it always, gets the defaults
                            kw = self.default_kwargs.copy()
                            for (name,val) in zip(self.argnames,args):
                                kw[name]=val
                            kw.update(kwargs)
                            kwargs=kw
                        
                        self.kwargs = kwargs
                        self._txt = '{}(**{})'.format(self.name, kwargs)
                    def __call__(self,N=1):
                        ret = self._fn(size=N, **self.kwargs)
                        return ret
                    def __str__(self):
                        return self._txt
                    __repr__=__str__
                
                RandomDistribution._fn=f
                RandomDistribution.name=n
                RandomDistribution.desc=desc
                RandomDistribution.argnames=argnames
                RandomDistribution.argvals=argvals
                RandomDistribution.default_kwargs = dict(zip(argnames,argvals))
                
                x[n] = RandomDistribution
                #x.append((n,desc,f,argnames,argvals))
        except Exception as e:
            #print(e)
            pass
    return x
_np_random_info = parse_numpy_random()

def RandomDistribution(name,*args,**kwargs):
    # see parse_numpy_random, or ignore this (because it isn't really used)
    cls = _np_random_info[name]
    return cls(*args,**kwargs)
    
'''
class RandomDistribution(object):
    def __init__(self,name,*args,**kwargs):
        self.name = name
        self.args = args        
        self.kwargs = kwargs
        self._fn = getattr(np.random,name)
        self._txt = '{}(**{})'.format(name, kwargs)
    def __call__(self,N):
        return self._fn(size=N, **self.kwargs)
    def __str__(self):
        return self._txt
    __repr__=__str__
'''
class RandomDistributionWidget(PickerWidget):
    '''
    picker widget for random distributions available in Numpy.  Not used in
    the current project, but pretty neat?
    '''
    default_value = RandomDistribution('normal')
    def __init__(self,*args,**kwargs):
        PickerWidget.__init__(self,*args,**kwargs)
        for info in _np_random_info.values():
            with self.add(info.name) as add:
                add('', QLabel(info.desc),store=False)
                for k,v in zip(info.argnames,info.argvals):
                    add(k,val=v)
        '''
        for (name, desc, f, argnames, argvals) in self._methods:
            with self.add(name) as add:
                add('', QLabel(desc),store=False)
                for k,v in zip(argnames,argvals):
                    add(k,val=v)
        '''
        
        self.build_layout()
    def _parseConfig(self, opt, config):
        return RandomDistribution(opt,**config)    
    def _makeConfig(self, value):
        return (value.name, value.kwargs)
"""
class NoiseMaker(object):
    def __init__(self,txt,fn,**kwargs):
        self._fn = fn
        self._txt = txt
        self._kwargs=kwargs
    def __call__(self, N=1):
        return self._fn(size=N, **self._kwargs)
    def __str__(self):
        return self._txt
    __repr__ = __str__

def NoiseMakers():
    def gaussian(u,s):
        '''
        A Gaussian (normal) distribution
        '''
        return NoiseMaker('Gaussian',np.random.normal,loc=u,scale=sd)
    return locals()
NoiseMakers=NoiseMakers()

class NoiseWidget(PickerWidget):
    default_value = NoiseMakers['gaussian'](0,1)
        
    def __init__(self,*args,**kwargs):
        PickerWidget.__init__(self,*args,**kwargs)
        for name,maker in NoiseMakers.items():
            with self.add(name) as add:
                add('',QLabel(maker.__doc__),store=False)
                add('mean',v=0)
                add('standard deviation', val=1)
        self.build_layout
"""