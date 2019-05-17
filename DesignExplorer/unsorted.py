from __future__ import absolute_import
from .common import *

valid_regression_modes=('','AM1','AM2','IM')

class DesignTable(Table):
    '''
    base class for PartsTable and ConfigTable
    '''
    def getNames(self):
        return [p['name'] for p in self.data()]
    def _sortedNames(self,design,what,backup_names):
        try:
            prev_names = design.userOrdering(what)
        except KeyError:
            return backup_names
        
        # cannot use old order if there are new names
        unexpected = set(backup_names) - set(prev_names)
        unexpected -= set(['experiment']) # ignore 'experiment', it is a default part currently
        if unexpected:
            return backup_names
        return prev_names
    
    def sortByNames(self,names):
        current_names = self.getNames()
        order = [current_names.index(name) for name in names]
        self.reorder(order)




class DistPickerWidget(PickerWidget):
    default_value = 0
    #clean: this was already icky, but had to hardcode it for now since that way didn't even work!
    _dist_names=('Const','Exp','Uni','Custom')
    _dist_types=(Dist.Const, Dist.Exp, Dist.Uni, Dist.Custom)
    #_dist_props=(('lo','mean','hi','nice','group'),('lo','mean','hi','nice','group'),('lo','mean','hi','nice','group'))
    #_dist_names = tuple([d for d in dir(Dist) if not d.startswith('_')])
    #_dist_types = tuple([getattr(Dist,n) for n in _dist_names])
    #_dist_props = tuple([[d for d in dir(t) if not d.startswith('_')] for t in _dist_types])
    
    def __init__(self,*args,**kwargs):
        PickerWidget.__init__(self,*args,**kwargs)
        self.setFixedSize(300,350)
        with self.add('Const') as add:
            add('val',val=0.0, tip='Enter a constant interval')
        with self.add('Uni') as add:
            add('lo',val=0.0, tip='Enter shortest duration for uniform distribution')
            add('hi',val=0.0, tip='Enter longest duration for uniform distribution')
            add('nice',QCheckBox(),val=True, tip='blah blah blah')
            add('group',val='')
        with self.add('Exp') as add:
            add('lo',val=0.0, tip='Enter shortest duration for exponential distribution')
            add('mean',val=0.0, tip='Enter mean duration for exponential distribution')
            add('hi',val=0.0, tip='Enter longest duration for exponential distribution')
            add('nice',QCheckBox(),val=True, tip='blah blah blah')
            add('group',val='')
        with self.add('Custom') as add:
            add('values', get=lambda w: Widget.values(w,float), tip='Enter custom distribution')
            #idea: someething like this?
            #add('values',val=[])
            
        layout = self.build_layout()
        info = QLabel()
        info.setWordWrap(True)
        info.setText(dedent('''
            Choose a distribution for timings
               (all values are in seconds)   
        '''))
        appendStyleSheet(info,'''QLabel {border-top: 1px solid #666666}''')
        layout.addWidget(info)

    def _validateValue(self,value):
        if type(value).__name__ not in self._dist_names:
            value = Dist.Const(value)         
        return value
        
    def _reprValue(self,value):
        #clean: even with abbreviations, dist specs can get very long.  how can I present it better?
        # would it be worth using args not kwargs where possible? omit default values? combine inter/pre/post
        # since simultaneous use is rareish?
        if type(value).__name__ == 'Const':
            return str(value.mean)
        if type(value).__name__ == 'Custom':
            return 'custom'
            return str(value.values)
        
        # remove Dist. prefix
        txt=str(value)[5:]
        # remove default values
        txt=txt.replace(',nice=True','').replace(',group=None','')
        return txt
    
    def _parseConfig(self,opt,config):
        if config.get('group',None)=='':
            config['group']=None
        dist=getattr(Dist,opt)
        return dist(**config)
    
    def _makeConfig(self, value):
        i=self._dist_names.index(type(value).__name__)
        opt=self._dist_names[i]
        if opt=='Const':
            config=dict(val=value.mean)
        elif opt=='Custom':
            config=dict(values=value.values)
        else:
            config=dict([(p,getattr(value,p)) for p in ('lo','mean','hi','nice','group')])
            if config.get('group',7)==None:
                config['group']=''
        return (opt,config)

class ModelPickerWidget(PickerWidget):
    default_value = ''
    def __init__(self,*args,**kwargs):
        PickerWidget.__init__(self,*args,**kwargs)
        self.setFixedSize(400,500)
        #self._format=dict()
        with self.add('NONE') as add:
            add('',QLabel('''This event does not currently have a regressor.  You can select a model from the drop down list above or leave it unmodeled.'''),store=False,wrap=True)
        with self.add('BLOCK') as add:
            add('',QLabel(dedent('''
                A simple boxcar regressor
            ''')),store=False)
            add('duration',val=1.0, tip='Enter duration of event')
            add('amplitude',val=1.0, tip='Enter an amplitude')
            #self._format['BLOCK']='BLOCK({duration},{amplitude})'
        with self.add('dmBLOCK') as add:
            add('',QLabel(dedent('''
                A boxcar regressor with a duration that varies. Requires the AM1 or AM2 regression mode.

                The durations will be set to match however long the event is for each occurrence.
            ''')),store=False, wrap=True)
            add('amplitude',val=1.0, tip='Enter an amplitude')
            #self._format['dmBLOCK']='dmBLOCK({amplitude})'
        with self.add('GAM') as add:
            add('',QLabel(dedent('''
                Single parameter gamma variate
                
                With p=amplitude and q=tuning factor:
                    (t/(p*q))^p * exp(p-t/q)                
                    
                    The peak will be at time p*q after the stimulus.
                    The FWHM is about 2.3*sqrt(p)*q.
                
                If you specify duration, this response will be convolved with
                a square wave of that duration.
            ''')),store=False, wrap=True)
            
            add('amplitude',val=8.6, tip='Enter an amplitude')
            add('q',val=0.547, tip='Enter the tuning factor')
            add('duration',val=0.0, tip='Enter duration of event')
            #self._format['GAM']='GAM({amplitude},{q},{duration})
        with self.add('CSPLIN') as add:
            add('',QLabel(dedent('''
                n parameter cubic spline function expansion from times b..c after stimulus time.
            ''')),store=False, wrap=True)
            sb=QSpinBox()
            sb.setMinimum(4)
            sb.setValue(4)
            add('n',sb, val=4, tip='Enter number of estimates')
            add('b',val=0.0, tip='Enter beginning time')
            add('c',val=1.0, tip='Enter ending time')
        with self.add('CUSTOM') as add:
            add('',QLabel(dedent('''
                There are a lot more response models available in AFNI, I didn't bother making a form for all of them... but you can type it in yourself (using AFNI's syntax) and it should work.
                
                For example, you could use this instead of the BLOCK option to accomplish the same thing.
                
                BLOCK(1,2) is a simple boxcar regressor with duration 1 and amplitude 2.
            ''')),store=False, wrap=True)
            
            add('model',val='BLOCK(1,2)', tip='Enter a custom AFNI model')
        
        layout = self.build_layout()
        info = QLabel()
        info.setWordWrap(True)
        info.setText(dedent('''All times are in seconds'''))
        appendStyleSheet(info,'''QLabel {border-top: 1px solid #666666}''')
        layout.addWidget(info)
        ahelp = QLabel()
        ahelp.setWordWrap(True)
        ahelp.setText('''<a href=https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dDeconvolve.html>See the AFNI help file learn more about
            response models</a>''')
        ahelp.setOpenExternalLinks(True)
        layout.addWidget(ahelp)
        
    def _parseConfig(self,opt,kwargs):
        if opt=='NONE':
            return ''
        if opt=='BLOCK':
            return 'BLOCK({duration},{amplitude})'.format(**kwargs)
        if opt=='dmBLOCK':
            return 'dmBLOCK({amplitude})'.format(**kwargs)
        if opt=='GAM':
            d = kwargs.get('duration',0)
            if d:
                return 'GAM({amplitude},{q},{duration})'.format(**kwargs)
            return 'GAM({amplitude},{q})'.format(**kwargs)
        if opt=='CSPLIN':
            return 'CSPLIN({b},{c},{n})'.format(**kwargs)
        raise NotImplementedError('unable to parse configuration {} + {}'.format(opt,kwargs))
        
    def _makeConfig(self,value):
        if not value:
            return ('NONE',{})
        
        (opt,vals)=value.strip().split('(')
        vals=vals[:-1].split(',')
        
        if opt=='BLOCK':
            names=('duration','amplitude')
        elif opt=='dmBLOCK':
            names=('amplitude',)
        elif opt=='GAM':
            if len(vals)==2:
                names=('amplitude','q')
            else:
                names=('amplitude','q','duration')
        elif opt=='CSPLIN':
            names=('b','c','n')
        else:
            raise NotImplementedError('unhandled configuration option value {}'.format(value))
        
        config = dict(zip(names,vals))
        
        return (opt,config)
        
        
    def _parseValue(self,value):
        if not value:
            value=''
        return (value,value)

        
class ConfigRow(Row):
    col_names=['remove','copy']+'name,type,N,dist,dur,model,regression_mode,max_consec,pre,inter,post'.split(',')
    def __init__(self,owner):
        Row.__init__(self,owner)
        with self.build as add:
            
            add('name', tip='Name of event')
            add('type', tip='Different event types (as in different conditions)')
            add('N',get=Widget.as_ints,val=1, tip='Number of events')
            add('pre', PickerButton(DistPickerWidget(),parent=self.table), val=0, get=Widget.value, tip='Enter a pre-event interval')
            add('inter', PickerButton(DistPickerWidget(),parent=self.table), val=0, get=Widget.value, tip='Enter inter-event interval')
            add('post', PickerButton(DistPickerWidget(),parent=self.table), val=0, get=Widget.value, tip='Enter a post-event interval')
            add('dur', PickerButton(DistPickerWidget(),parent=self.table), val=1, get=Widget.value, tip='Enter event duration')
            add('dist',get=Widget.as_floats, val=0)
            add('max_consec',get=Widget.as_ints, val=0, tip='Maximum consecutive event types')
            add('model',PickerButton(ModelPickerWidget(),parent=self.table), val="", tip='Choose hemodynamic response function')
            
            w=QComboBox()
            w.setStyle(QtGui.QStyleFactory.create('Cleanlooks'))
            appendStyleSheet(w,'''
                .QComboBox {
                    background-color: #f2f2f2;
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
            for mode in valid_regression_modes:
                w.addItem(mode)
            # to do: change regression mode choice to model widget
            add('regression_mode',w,get=Widget.as_str, tip='Choose a regression mode')



class ConfigTable(DesignTable):
    col_names = ConfigRow.col_names
    def __init__(self,owner,*args,**kwargs):
        DesignTable.__init__(self,owner,ConfigRow,*args, **kwargs)
    
    def parse(self):
        configs=self.data()
        
        # validation
        entries=set([])
        for i,config in enumerate(configs):
            entry = config['name']+'.'+config['type']
            if entry not in entries:
                entries.add(entry)
            else:
                raise Exception('row {} conflicts with an earlier row'.format(i+1))
        
        # build the config
        config=Config()
        for c in configs:
            name=c.pop('name')
            if name:
                ty=c.pop('type')
                if ty:
                    name=ty+'.'+name
                config[name] = c
                
        return config
    
    def getNames(self):
        configs = self.data()
        names=[]
        for c in configs:
            name = c['name']
            ty = c['type']
            if ty:
                name=ty+'.'+name
            names.append(name)
        return names
    
    def load(self, design):
        with signalsBlocked(self):
            self.clear()
            if design and design.valid():
                config = design.config()
                
                names = self._sortedNames(design,'design_config',list(config))            
                for name in names:
                    d = config[name].copy()
                    d['name'] = name
                    row = self.add()
                    row.set_data(d)
        self.tableDataChangedEvent()

class QPlaceholder(QVBoxLayout):
    '''
    A placeholder for a QWidget or QLayout.  Use the 'item' property to get or set
    what widget should be shown.  or empty() to clear it.
    
    Unless QPlaceholder owns the item, you must either close it or reparent it yourself.
    Otherwise it'll still be rendered as before for some reason...
    
    #doc:
    '''
    def __init__(self,default_owns=False):
        QVBoxLayout.__init__(self)
        self._default_owns = default_owns
        self._initPlaceholder()
    
    def _initPlaceholder(self):
        self._owns = True
        self._empty = True
        self._item = QWidget()
        self.addWidget(self._item)
    
    def _removeItem(self):
        old = self._item
        if isinstance(old,QWidget):
            self.removeWidget(old)
            if self._owns:
                old.close()
                return None
            else:
                return old
        elif isinstance(old,QLayout):
            self.removeItem(old)
            return old
    #clean: rename to clear
    def empty(self):
        '''
        removes the held item and returns it (or None if empty already).
        It is your responsibility to call close if appropriate
        '''
        if self._empty:
            return None # already empty
        ret = self._removeItem()
        self._initPlaceholder()
        self.update()
        return ret
    
    @property
    def item(self):
        if self._empty:
            return None
        else:
            return self._item
    
    @item.setter
    def item(self,new):
        if new is None:
            self.empty()
        else:
            self._removeItem()
            self._owns = self._default_owns
            self._empty = False
            self._item = new
            if isinstance(new,QWidget):
                self.addWidget(new)
            elif isinstance(new,QLayout):
                self.addLayout(new)
            else:
                self.empty()
                raise TypeError('item must be QWidget, QLayout, or None')
            
            self.update()




########################################################################################################
## style stuff            


