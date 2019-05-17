from __future__ import absolute_import
from .common import *
'''
stuff related to matplotlib 
'''

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
try:
    from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
except ImportError:
    from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar

from matplotlib.backends.backend_qt4agg import new_figure_manager_given_figure
from matplotlib.figure import Figure


#the matplotlib devs didn't fix this for some reason, didn't really
# pay much attention to the discussion... but this solution as posted
# by the OP works.  now panning is smoother.  
#fixme: are we requiring qt?  Probably... but should at least
# check if qt is available.  Better to raise a descriptive exception than
# to crash on something as obscure as this patch function...
def patch_qt4agg():
    import matplotlib.backends.backend_qt4agg as backend
    code = """
def draw( self ):
    FigureCanvasAgg.draw(self)
    self.repaint()
FigureCanvasQTAgg.draw = draw    
"""
    exec(code, backend.__dict__)
patch_qt4agg()


#opt: is this a performance issue?  probably not, as only called when data actually changes?  still may be worth checking.
def redraw_canvas(canvas):
    # don't recall if this is used outside of Figure Widget...
    canvas.resizeEvent(QResizeEvent(canvas.size(),canvas.size()))
#annoy: have to reference axes directly to do plotting, no convenience of gcf since the figures aren't managed in that way when created manually from Figure...
#idea: new_figure_manager_given_figure !!! might this fix things!?  WHY NOT IN EXAMPLES!?"@<
class FigureWidget(FigureCanvas):
    '''
    matplotlib figure widget, should take care of all the nonsense developers don't actually 
    want to care about!  Use this if you want to plot something (via matplotlib)
    as a widget in Qt.
    '''
    def __init__(self, parent=None, *args, **kwargs):
        self.fig = Figure(*args,**kwargs)
        FigureCanvas.__init__(self,self.fig)
        self.setParent(parent)
        
        self._first_draw_cid = self.fig.canvas.mpl_connect('draw_event', self._first_draw)
        
        
        #self.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
        # ignored seems to be the answer.  other policies are confusing and cause problems
        # when there is nesting (like a scroll area).  This just makes it work.
        self.setSizePolicy(QSizePolicy.Ignored,QSizePolicy.Ignored)
        
        #idea: on double click, maximize the clicked axes or restore it to previous size.  
    
    def _first_draw(self,event):
        self.fig.canvas.mpl_disconnect(self._first_draw_cid)
        #print('first draw',self.get_width_height())
        self.updateGeometry()
        #print('first draw after geo',self.get_width_height())
        #impl:
    '''
    def __enter__(self):
        g=plt._pylab_helpers.Gcf
        self._prev_active = g._activeQueue
        self.fig.canvas.activateWindow()
        g._activeQueue = [self.fig]
        return self
    def __exit__(self,*args):
        g=plt._pylab_helpers.Gcf
        g._activeQueue = self._prev_active
    '''
    
    @perr
    def sizeHint(self):
        (w,h) = self.get_width_height()
        #self.setMaximumSize(*self.minimumSizeHint())
        #print('size hint',w,h)
        return QSize(w,h)
    
    @perr
    def minimumSizeHint(self):
        #return QSize(10,10)
        (w,h) = self.get_width_height()
        w = max(w,30)
        h = max(h,30)
        #print('min size hint',w,h)
        return QSize(w,h)
    
    def redraw(self):
        #print('redraw!')
        redraw_canvas(self.fig.canvas)


class ArtistStyleWidget(FigureWidget):
    '''
    A qt Widget that represents a maplotlib style (style, color, marker).
    
    Able to access/change the value via value and text methods
    
    plots the style.
    
    '''
    def __init__(self,*args,**kwargs):
        FigureWidget.__init__(self)
        self.ax =self.fig.add_subplot(111)
        
        # hide everything
        for item in [self.fig, self.ax]:
            item.patch.set_visible(False)
        self.ax.axes.get_xaxis().set_visible(False)
        self.ax.axes.get_yaxis().set_visible(False)
        for spine in self.ax.spines.values():
            spine.set_visible(False)
        
        # by default, stay at the ideal size...
        
        #self.setSizePolicy(QSizePolicy.Minimum,QSizePolicy.Minimum)
        #self.fig.canvas.setSizePolicy(QSizePolicy.Minimum,QSizePolicy.Minimum)
        #self.setSizePolicy(QSizePolicy.Minimum,QSizePolicy.Minimum)
        #self.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
        #self.fig.canvas.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Fixed)
        
        self.config(*args,**kwargs)        
    
    def config(self,spec=None,kind='line',**kwargs):        
        try:
            self.leg.remove()
            first=False
        except:
            first=True
            pass
        
        if spec:
            (A,B)=(spec,kwargs)
            kwargs.update(plot_format(spec,kind=kind))
        else:
            (A,B) = plot_unformat(**kwargs)        
        B = ', '.join(['{}={}'.format(k,repr(v)) for (k,v) in B.items()])
        
        if A and B:
            txt = A+', '+B
        elif A:
            txt = A
        else:
            txt = B
        
        label = kwargs.pop('label','')
        leg_kwargs = kwargs.pop('legend_kwargs',{})
        leg_kwargs['frameon']=False
        leg_kwargs['loc']=10
        
        leg = self.ax.legend([example_artist(kind=kind,**kwargs)],[label],**leg_kwargs)
        
        lbb = leg.get_window_extent()
        fbb = self.fig.bbox
        fbbi = self.fig.bbox_inches
        
        w = fbbi.width * (lbb.width/fbb.width)
        h = fbbi.height * (lbb.height/fbb.height)
        self.fig.set_size_inches(w,h,forward=True)
        
        #finally, this seems to work!
        #annoy: wait no??  then what fixed this nonsense??
        '''
        (w,h) = (self.fig.bbox.width,self.fig.bbox.height)
        w = w*1.05+100
        h = h*1.05+100
        self.fig.canvas.resize(QSize(w,h))
        '''
        self.leg = leg
        
        
        if spec or kwargs:
            self._value = kwargs
            self._txt = txt
        else:
            self._value={}
            self._txt=''
        
        # redraw workaround has some issues, so another workaround!
        if not first:
            self.redraw()
        #testing:
        self.updateGeometry()
        
    def text(self):
        return self._txt
    def setText(self,txt):
        txt=txt.strip()
        # nothing!
        if not txt:
            self.config()
            return
        
        parts = txt.split(',')
        if '=' not in parts[0]:
            spec=parts[0]
            parts=parts[1:]
            
            spec=spec.replace('"','').replace("'",'')
        else:
            spec=''
        
        kwargs=dict()
        for part in parts:
            (k,v) = part.split('=')
            k=k.strip()
            v=v.strip()
            kwargs[k]=v
        
        self.config(spec,**kwargs)
    
    def value(self):
        return self._value
    def setValue(self,value):
        self.config(**value)
    
    def __str__(self):
        return self._txt
    __repr__ = __str__
        
        
        

class StyleConfigWidget(BetterWidget):
    '''
    A widget representing a multiple matplotlib plot style (style, color, marker).
    holds a dictionary of styles
    '''
    def __init__(self,config):
        BetterWidget.__init__(self)
        
        self.config = config
        grid = QGridLayout()
        self.widgets=dict()
        
        def add_row(i,k):
            v = config[k]
            tw = QLineEdit()
            sw = ArtistStyleWidget(**v)
            tw.setText(sw.text())
            config[k]=sw.value()
            tw.setSizePolicy(QSizePolicy.Maximum,QSizePolicy.Maximum)
            sw.setSizePolicy(QSizePolicy.Minimum,QSizePolicy.Minimum)
            connect(Widget.signal(tw),lambda txt: self._onEdit(k,sw,txt))
                        
            grid.addWidget(QLabel(k),i,0)
            grid.addWidget(tw,i,2)            
            grid.addWidget(sw,i,1)
            self.widgets[k] = (tw,sw)
        
        for i,k in enumerate(config.keys()):
            add_row(i,k)
        
        self.setLayout(grid)
    def refresh(self):
        for name,style in self.config.items():
            (tw,sw) = self.widgets[name]
            sw.config(**style)
            with signalsBlocked(tw):
                tw.setText(sw.text())
    @perr
    def _onEdit(self, name, style_widget, txt):
        try:
            style_widget.setText(txt)
        except Exception as e:
            return
        self.config[name]=style_widget.value()
        
    
class axisLimitLock(object):
    def __init__(self,ax,which,width=None):
        self._ax = ax
        self._which = which
        self._width = width
        self._locked=False
        self.lock()
    def lock(self):
        if self._locked:
            return
        self._locked=True
        self._rules = axisLimitRules(self._ax, self._which, width=self._width)
    def unlock(self):
        if not self._locked:
            return
        self._locked=False
        self._rules.disconnect()

#clean: don't need lock, can just emit=False I think.
class axisLimitRules(object):
    def __init__(self, ax, which, lo=None, hi=None, width=None):
        self._ax = ax
        if 'x' in which:
            changed = 'xlim_changed'
            self._get_lim = ax.get_xlim
            self._set_lim = ax.set_xlim
        else:
            changed = 'ylim_changed'
            self._get_lim = ax.get_ylim
            self._set_lim = ax.set_ylim
        
        
        self._lock = False
        self._cid = ax.callbacks.connect(changed,self)
        
        if lo is None:
            lo = self._get_lim()[0]
        if hi is None:
            hi = self._get_lim()[1]
        if width is None:
            width = hi-lo
        
        self.lo=lo
        self.hi=hi
        self.width=width        
        self()
    def disconnect(self):
        try:
            self._ax.callbacks.disconnect(self._cid)
        except:
            pass
    
    def __call__(self,event=None):
        if self._lock:
            return
        self._lock=True
        
        lo=self.lo
        hi=self.hi
        width=self.width
        
        (a,b) = self._get_lim()
        if a>=b:
            (a,b) = (lo,lo+width)
        
        if a<lo:
            a=lo
        elif a>hi-width:
            a=hi-width
        
        if b<lo+width:
            b=lo+width
        elif b>hi:
            b=hi
        
        self._set_lim(a,b)
        
        self._lock=False
            


#annoy: what a mess.  Probably easier to redo the navigation toolbar myself than to try and use
# the mess provided in matplotlib...  I just want to restrict the axes limits...  
class enablePanZoom(object):
    def __init__(self,f,axes,xlim,ylim):
        self.xlim=xlim
        self.ylim=ylim
        #self.xlim=self._parse(xlim)
        #self.ylim=self._parse(ylim)
        self._f = f
        self._axes=axes
        self._lock=False
        
        self._tb = NavigationToolbar(f.canvas,None)
        self._tb.pan()
        self._cids=[]
        for ax in axes:
            a=ax.callbacks.connect('ylim_changed',self)
            b=ax.callbacks.connect('xlim_changed',self)
            self._cids.append((ax,a))
            self._cids.append((ax,b))
        
        self._cid = f.canvas.mpl_connect('button_press_event',self.reset)
    
    def disconnect(self):
        for ax,cid in self._cids:
            try:
                ax.callbacks.disconnect(cid)
            except:
                pass
        try:
            self._f.canvas.mpl_disconnect(self._cid)
        except:
            pass
        
        self._tb.close()
    
    close=disconnect
    
    def reset(self,event):
        if event.dblclick:
            self._axes[0].set_xlim(self.xlim[0],self.xlim[1])
            self._axes[0].set_ylim(self.ylim[0],self.ylim[1])
            
            ax.set_xlim(0,1000)
            ax.set_ylim(0,9)
    ''' 
    def _parse(self,lim):
        N=len(lim)
        if N==1:
            raise NotImplementedError("can't just specify a width")
        if N==2:
            return (lim[0],lim[1],lim[1]-lim[0])
        if N==3:
            return lim
        raise ValueError('limits must be of length 2 or 3')
    '''
    def _clamp(self,a,b,lim):
        
        (lo,hi,width) = lim
        #idea: auto clamp to data ranges... but that's a lot of calculations to do...
        '''
        try:
            (lo,hi,width) = lim
        except:
            if not lim:
                return
            
            (lo,hi)
        '''
        if a>=b:
            return (lo,lo+width)
        
        if a<lo:
            a=lo
        elif a>hi-width:
            a=hi-width
        
        if b<lo+width:
            b=lo+width
        elif b>hi:
            b=hi
            
        return (a,b)
    
    #opt: redrawing here is rather slow...  surely there is something I can do about it (though better solutions would have to come from the matplotlib devs)
    def __call__(self,ax):
        if self._lock:
            return
        self._lock=True
        
        (x0,x1) = ax.get_xlim()
        (x0,x1) = self._clamp(x0,x1,self.xlim)
        
        (y0,y1) = ax.get_ylim()
        (y0,y1) = self._clamp(y0,y1,self.ylim)
        
        for ax in self._axes:
            ax.set_xlim(x0,x1)
            ax.set_ylim(y0,y1)
        
        self._lock=False





# still in testing, see EXPLORATION folder.  this is just a useable snapshot.
def fast_redraw(a, copy_legend=True):
    '''
    A much faster redraw for when you change plot data.  
    '''
    f = a.get_figure()
    c = f.canvas
    
    if copy_legend:
        legend = a.legend_
    else:
        legend = None
    
    if legend is not None:
        bb =  legend.legendPatch.get_bbox() # would need a helper if I wanted to try caching this...
        legend_copy =c.copy_from_bbox(bb)
        a.legend_=None
    '''
    # this is the first way I tried... not a noticable improvement over just drawing inframe.
    if _children_only:
        cs=[(c.zorder,c) for c in a.get_children()]
        cs.sort(key=lambda x: x[0])
        (_,artists) = zip(*cs)
        
        for artist in artists:
            if isinstance(artist, mpl.axis.Axis):
                continue
            a.draw_artist(artist)
    else:
    '''
    a.draw(renderer=None,inframe=True)
    
    if legend is not None:
        a.legend_=legend
        c.restore_region(legend_copy)
    
    c.update()
    c.flush_events()



def niceStyles(names, colors=None, styles=None, markers=None):
    '''
    attempts to assign good default colors and linestyles to given names.
    not particularly generic or complete.  but it tries.  Seems to work
    well for simple type+name event designs.
    
    markers are not handled
    '''
    ret=dict()
    if colors is None:
        colors = 'grcmybk'
    if styles is None:
        styles = ('-','--','-.',':')
    
    try:
        (A,B) = zip(*[name.split('.') for name in names])
    except:
        return ret
    
    uA = set(A)
    uB = set(B)
    nA = len(uA)
    nB = len(uB)
    
    mA=dict()
    mB=dict()
    
    def helper(ks,vs,what):
        ret=dict()
        for k,v in zip(ks,vs):
            ret[k]={what:v}
        return ret
    #idea: if I really really want to spend the time, I can probably
    # implement better heuristics.
    
    if nA<=len(colors) and nB<=len(styles):
        mA=helper(uA,colors,'color')
        mB=helper(uB,styles,'linestyle')
    elif nB<=len(colors) and nA<=len(styles):
        mB=helper(uB,colors,'color')
        mA=helper(uA,styles,'linestyle')
    else:
        return ret
    
    
    for a,b in zip(A,B):
        d=dict(mA[a])
        d.update(mB[b])
        ret[a+'.'+b]=d
    
    return ret

class StylesGUI(BetterDialog):
    '''
    give it a design and it'll help the user configure the plot styles
    '''
    
    def __init__(self,design, *args,**kwargs):
        BetterDialog.__init__(self,*args,**kwargs)
        self.design = design
        (first,rest) = design.eventNames()
        self.first = first
        self.rest = rest
        self.names = names = first + rest
        
        self.config = c = OrderedDict()
        for i,name in enumerate(names):
            c[name] = design.style(i)
        
        self.widget = w = StyleConfigWidget(c)
        
        lay = QVBoxLayout()
        bot = QHBoxLayout()
        lay.addWidget(w)
        lay.addLayout(bot)
        
        def add(name):
            b = QPushButton()
            b.setText(name)
            bot.addWidget(b)
            cb = getattr(self,'on'+name.capitalize())
            connect(b.clicked,lambda unused: cb())
        
        add('OK')
        add('cancel')
        add('auto')
        
        self.setLayout(lay)
    
    def onOk(self):
        ls=[]
        ms=[]
        cs=[]
        for name in self.names:
            d = self.config[name]
            ls.append(d['linestyle'])
            ms.append(d.get('marker','None'))
            cs.append(d['color'])
        self.design.setStyles(linestyles=ls, markers=ms, colors=cs)
        self.accept()
    def onCancel(self):
        self.reject()
    def onAuto(self):
        nice = niceStyles(self.first)
        self.config.update(nice)
        self.widget.refresh()

#testing: pulled this from 'jkpy.unfinished'.  if improved, should be put back there or promoted
def hexbin(*args,**kwargs):
    ax = kwargs.pop('ax',None)
    #idea: default gridsize and bins based on given data
    ret=None
    N=len(args)
    if N==3:
        (x,y,z)=args
    elif N==2:
        (x,y)=args
        if np.ndim(y)==2:
            y = y.ravel()
            x = np.tile(x,len(y)/len(x))            
        ret=ax.hexbin(x,y,**kwargs)            
    elif N==1:
        z=args[0]
        x=np.arange(0,z.shape[0])
        if np.ndim(z)==2:
            y=np.arange(0,z.shape[1])
        else:
            y=x
    else:
        raise TypeError('hexbin() takes up to 3 non-keyword arguments ({} given)'.format(N))
    
    if ret is None:
        if np.ndim(z)==2:
            #idea: more valid combinations here, but... useful?
            if np.ndim(x)==1:
                (x,y)=np.meshgrid(x,y)
            x=x.ravel()
            y=y.ravel()
            z=z.ravel()
        
        ret=ax.hexbin(x,y,C=z,**kwargs)
    
    #plt.axis([x.min(),x.max(),y.min(),y.max()])    
    #if cbar:
    #    plt.colorbar()
    
    return ret

class ConvenientAxes(object):
    def __init__(self,ax,pan=False,resize=False,fast=False,limit=False):
        #idea: make ax a property, allow for changing
        #idea: lots of kwargs for init, maybe helper function for making new classes
        # with specific settings for quick reuse?
        self.ax = ax
        self.fig = ax.get_figure()
        self.canvas = self.fig.canvas
        # lots of convenient features implemented already, easier to resuse them
        # even if not actually displaying the toolbar
        self._tb = self.toolbar_widget = NavigationToolbar(self.canvas,None)
        
        self._pan = False
        self._use_locks = False
        self._context_options = None
        self.config(pan=pan,resize=resize,fast=fast,limit=limit)
    
    def config(self,pan=False,resize=False,fast=False,limit=False):
        if self._context_options:
            raise Exception('not allowed to reconfigure while locked')
        if self._pan != pan:
            self._tb.pan()
            self._pan = pan
        if self._use_locks and self._locks and not limit:
            self._locks = None
        self._use_locks = limit
        self._options = dict(resize=resize,fast=fast)
    
    def clear(self):
        self._locks = None
        self.ax.clear()
    def __call__(self,**options):
        self._context_options = set_defaults(options,self._options)
        return self
    
    def lock(self):
        if self._use_locks and self._locks:
            for lock in self._locks:
                lock.unlock()
        return self.ax
    def unlock(self,*unused):
        if not self._context_options:
            self._context_options = self._options
        
        if self._use_locks:
            if self._locks:
                for lock in self._locks:
                    lock.lock()
            else:
                self._locks = (axisLimitLock(self.ax,'x',width=1),axisLimitLock(self.ax,'y'))
        
        if self._context_options['resize']:
            self.ax.relim()
            self.ax.autoscale_view()
            self.canvas.draw()
        
        if self._context_options['fast']:
            fast_redraw(self.ax,copy_legend=True)
        
        self._context_options = None
    
    __enter__=lock
    __exit__=unlock
    
    
