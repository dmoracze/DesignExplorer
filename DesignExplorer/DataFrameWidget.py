from __future__ import absolute_import
from .common import *

'''
still need to update documentation for this...

a Qt widget for displaying pandas.DataFrames.  At least with regards to the needs
of the DesignExplorer project, this implementation is far better than similar offerings
found online.

soring, searching, filtering...

Not fully generic, I've only focused on applications wrt DesignExplorer.  But there
surely has potential for broader application.
'''

#moveup:
def npfindsorted(arr,val):
    '''
    like list.index, but assumes the given np.array is already sorted.
    '''
    i = arr.searchsorted(val)    
    try:
        if val==arr[i]:
            return i
    except IndexError:
        pass
    raise ValueError()
    #opt: ?  premature optimization?  but it does feel wrong to have an 'expensive' string formatting operation when often just catch the error and branch...
    #raise ValueError('{} is not in the array'.format(val))



#moveup:
from itertools import islice
class mrs_dict(MutableMapping):
    '''
    * ordered with most recently set item last (accessing the items doesn't reorder anything)
    * optional capacity, dropping least recently used items as needed
    * capacity can be changed anytime (is a property)
        
        
    Uses OrderedDict internally
        
    '''
    def __init__(self,*args,**kwargs):
        self._capacity = kwargs.pop('capacity',None)
        self._data = OrderedDict(*args,**kwargs)
        self._applyCapacity()
    @property
    def capacity(self):
        return self._capacity
    @capacity.setter
    def capacity(self,cap):
        self._capacity = cap
        self._applyCapacity()
    
    def _applyCapacity(self):
        # adjust capacity 
        if self._capacity:
            for i in range(len(self._data) - self._capacity):
                self._data.popitem(last=False)
        
    def __getitem__(self,k):
        return self._data[k]
    def __delitem__(self,k):
        del self._data[k]
    def __iter__(self):
        for y in self._data:
            yield y
    def __len__(self):
        return len(self._data)
    
    def __setitem__(self,k,v):
        if k in self._data:
            del self._data[k]
            self._data[k]=v
            return
        
        self._data[k]=v
        self._applyCapacity()
    
    #style: ?
    def at(self,i):
        #opt: annoying Py3...  how do I get the real slice syntax?  convert to islice maybe?
        return list(self.items())[i]
        #return next(islice(self.items(),i,None))
        #return self.items()[i]
        
        
    
    
    
                
            
        
    


class ColumnFilterWidgetItem(QListWidgetItem):
    def __init__(self):
        QListWidgetItem.__init__(self)
        self.i=None

#idea: add reset button
#idea: toggles for advanced features (regex=True, case=False)
class ColumnFilterWidget(QWidget):
    #changed = pyqtSignal()
    
    def __init__(self):
        QWidget.__init__(self)
        search = QLineEdit()
        search.textEdited.connect(self._on_search_changed)
        boxes = QListWidget()
        boxes.itemChanged.connect(self._on_checked)
        sall = QCheckBox()
        sall.setText('select all')
        Widget.signal(sall).connect(self._on_all_checked)
        clear_but = QPushButton()
        clear_but.setText('reset')        
        clear_but.clicked.connect(self._on_reset_clicked)
        
        layout = QVBoxLayout()
        layout.addWidget(search)
        layout.addWidget(clear_but)
        layout.addWidget(sall)
        layout.addWidget(boxes)
        self.setLayout(layout)
        
        self.boxes = boxes
        self.search = search
        self.sall = sall
    
    def clearConstraints(self):
        self._shown[:]=True
        self._selected[:]=True
        self.search.setText('')
        self._update()
        
    @perr
    def _on_reset_clicked(self,event):
        self.clearConstraints()
    
    def _update(self):
        self._on_search_changed(self.search.text())
    
    @property
    def shown(self):
        return self._shown[self._inds]
    @property
    def selected(self):
        return self._selected[self._inds]
    
    def reorder(self,perm):
        self._inds = self._inds[perm]
    
    def setValues(self,values, update=True):
        
        (new_values,new_inds) = np.unique(values,return_inverse=True)
        
        if update and hasattr(self,'_inds'):
            old_values = self._all_values
            old_selected = self._selected
            
            new_selected=np.ones(len(new_values),dtype=bool)
            for (i,val) in enumerate(new_values):
                try:
                    iold = npfindsorted(old_values,val)
                except ValueError:
                    new_selected[i] = True
                else:
                    new_selected[i] = old_selected[iold]
            
            self._selected = new_selected
        else:
            self._selected = np.ones(len(new_values),dtype=bool)
        
        self._all_values = new_values
        self._inds = new_inds
        self._shown = self._selected.copy()
        self._update()
    
    def _on_search_changed(self,txt):
        with Widget.signalsBlocked(self.boxes):
            # find which to show (also update _shown full mask)
            shown = []
            for (i,val) in enumerate(self._all_values):
                show = bool(re.search(txt,val,flags = re.IGNORECASE))
                if show:
                    shown.append((i,val))
                self._shown[i]=show
            
            # resize list to match
            N = len(shown)
            N0 = self.boxes.count()
            while N0<N:
                self.boxes.addItem(ColumnFilterWidgetItem())
                N0+=1
            while N0>N:
                self.boxes.takeItem(N0-1)
                N0-=1
            
            # configure the list items
            num_checked = 0
            self.num_shown = len(shown)
            for row,(i,val) in enumerate(shown):
                item = self.boxes.item(row)
                if self._selected[i]:
                    item.setCheckState(Qt.Checked)
                    num_checked+=1
                else:
                    item.setCheckState(Qt.Unchecked)
                item.setText(str(val))
                item.i = i
        self.num_checked = num_checked
        
        self._check_sall()
    
    def _check_sall(self):
        with Widget.signalsBlocked(self.sall):
            if self.num_checked == self.num_shown:
                self.sall.setCheckState(Qt.Checked)
            elif self.num_checked==0:
                self.sall.setCheckState(Qt.Unchecked)
            else:
                self.sall.setCheckState(Qt.PartiallyChecked)
            
    def _on_checked(self,item):
        if item.checkState():
            if self._selected[item.i]:
                return
            self._selected[item.i]=True
            self.num_checked += 1
        else:
            if not self._selected[item.i]:
                return
            self._selected[item.i]=False
            self.num_checked -= 1
        
        self._check_sall()
    
    def _on_all_checked(self,state):
        checked = state==Qt.Checked
        #fixme: sall was in tristate for some reason, and other items followed...
        with Widget.signalsBlocked(self.boxes):
            for row in range(self.num_shown):
                item = self.boxes.item(row)
                item.setCheckState(state)
                self._selected[item.i] = checked


def tableAutoWidth(table):
    w = 0
    t = table
    
    w += t.contentsMargins().left() + t.contentsMargins().right()
    #w += t.verticalHeader().width()
    w += t.verticalScrollBar().width()
    for i in range(t.columnCount()):
        w += t.columnWidth(i)
    t.setMinimumWidth(w)
    t.setMaximumWidth(w)
    
    # of course this doesn't work...
    #h = t.height()
    #t.resize(w,h)
    
    # doesn't work to unset the limits... just doesn't resize...
    #t.updateGeometry()
    #t.setMinimumWidth(0)
    #t.setMaximumWidth(16777215)


# has issues with cells that can't be selected, or that are disabled.  Like
# widgets embedded in the cell.  annoying...
def tableCopyEventFilter(table,event):
    if event.type()==QEvent.KeyPress and event.key()==Qt.Key_C and (event.modifiers() & Qt.ControlModifier):
        NC=table.columnCount()
        NR=table.rowCount()
        data = np.zeros((NR,NC),dtype=object)
        data[:]=''
        
        cells = table.selectedIndexes()
        for cell in cells:
            data[cell.row(),cell.column()]=cell.data()
        
        b = data.astype(bool)
        mr = b.any(1)
        mc = b.any(0)
        data = data[mr,:][:,mc]
        
        column_names = [table.horizontalHeaderItem(i).text() for i in mc.nonzero()[0]]
        lines=[]
        for line in [column_names] + data.tolist():
            line = '\t'.join('"'+val+'"' for val in line)
            lines.append(line)
        txt = '\n'.join(lines)
        QApplication.clipboard().setText(txt)
        return True



#moveup:
#idea: option to hide index (quite a pain to implement!  helps to cache more and include Nones rather than +1 -1 everywhere)
#idea: add support for editing
#idea: would like a generic table thing that has editing/filtering systems in place...  but every time I need something new, previous table implementations don't work... yuck.
#style: naming conventions are all over the place, C++ and Python development side by side makes a mess...  Soon take time to solidify conventions again.
class DataFrameWidget(QWidget):
    def __init__(self,df=None):
        QWidget.__init__(self)
        
        if df is None:
            df = pd.DataFrame()
        
        ncol = len(df.columns)
        
        table = QTableWidget(0,ncol+1)
        Widget.installEventFilter(table, tableCopyEventFilter)
        #table = MyTableWidget(0,ncol+1)
        #table.setSortingEnabled(True)
        
        filter_line = QLineEdit()
        filter_line.textEdited.connect(self._on_filter_changed)
        
        layout = QVBoxLayout()
        layout.addWidget(table)
        line = QHBoxLayout()
        line.addWidget(QLabel('query filter:'))
        line.addWidget(filter_line)
        w = QPushButton()
        w.setText('remove filters')
        w.clicked.connect(self._clearFilters)
        line.addWidget(w)
        #w = QPushButton()
        #w.setText('save as')
        #w.clicked.connect(self._save)
        #line.addWidget(w)
        layout.addLayout(line)
        self.setLayout(layout)
        
        header = table.horizontalHeader()
        header.setContextMenuPolicy(Qt.CustomContextMenu)
        header.customContextMenuRequested.connect(self.showHeaderContext)
        header.sectionClicked.connect(self._sort_click)
        
        self._table = table
        self._failing = False
        
        self._full_df = df
        self._viewed_df = df
        self._empty_df = pd.DataFrame(columns=df.columns)
        self._query_widget = filter_line
        
        self._sort_history = mrs_dict(capacity=ncol+1)
        
        self._filters = []
        self._filter_menus = []
        for i in range(ncol):
            self._pushFilterMenu(df,i)
        
        self._query_selected=True #np.ones(len(df),dtype=bool)
        
        #table.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
        #self.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
        self._update()
        #table.setSizePolicy(QSizePolicy.Preferred,QSizePolicy.Preferred)
        #self.setSizePolicy(QSizePolicy.Preferred,QSizePolicy.Preferred)
        
        
    #@perr
    #def sizeHint(self):
    #    return self._table.sizeHint()
    
    @perr
    def _clearFilters(self,event):
        self.clearFilters()
        
    def clearFilters(self):
        for f in self._filters:
            if f:
                f.clearConstraints()
        self._query_widget.setText('')
        self._on_filter_changed('')
        #self._failing = False
        #self._update()
    
    def _pushFilterMenu(self,df,i):
        if df.dtypes.values[i] == np.dtype('O'):
            w = ColumnFilterWidget()
            values = df.values[:,i]
            w.setValues(values)
            self._filters.append(w)
            
            m = QMenu()
            a = QWidgetAction(self)
            a.setDefaultWidget(w)
            m.addAction(a)
            self._filter_menus.append(m)
        else:
            self._filters.append(None)
            self._filter_menus.append(None)
    
    def setDataFrame(self,df):
        # save some old values
        old_columns = list(self._full_df.columns)
        old_filters = self._filters
        old_menus = self._filter_menus
        old_history = self._sort_history        
        
        # new dataframe
        new_columns = list(df.columns)
        new_history = mrs_dict(capacity = len(new_columns)+1)
        self._full_df = df
        self._viewed_df = df
        self._empty_df = pd.DataFrame(columns = df.columns)
        
        # migrate filter settings where possible
        self._filters=[]
        self._filter_menus=[]        
        for i,colname in enumerate(new_columns):
            try:
                oldi = old_columns.index(colname)
                menu = old_menus[oldi]
                f = old_filters[oldi]
            except (ValueError, IndexError):
                # need new filters
                self._pushFilterMenu(df,i)
            else:
                # try to keep old filters
                if f:
                    f.setValues(df[colname],update=True)
                self._filters.append(f)
                self._filter_menus.append(menu)
        
        # reapply the sorting
        for col in old_history:
            if col==0:
                newcol=0
            else:
                try:
                    newcol = new_columns.index(old_columns[col-1])+1
                except ValueError:
                    continue            
            new_history[newcol]=old_history[col]        
        self._sort_history = new_history
        if new_history:
            self._sort(new_history.keys(),new_history.values())
        
        self._table.setColumnCount(len(new_columns)+1)
        
        # finally update
        self._update()
        
        # and autosize it
        self._autoWidth()
    
    def _autoWidth(self):
        #annoy: what is with this offset??  confusing!
        for col in range(self._table.columnCount()-1):
            w = self.sizeHintForColumn(col)
            self._table.setColumnWidth(col+1,w)
        tableAutoWidth(self._table)
    
    # applies some number of column sorts (stable) in the given order
    def _sort(self,cols,ascs):
        header = self._table.horizontalHeader()
        header.setSortIndicator(cols[-1], Qt.AscendingOrder if ascs[-1] else Qt.DescendingOrder)
        header.setSortIndicatorShown(True)
        
        df = self._full_df
        cf = '_r_'
        df[cf] = np.arange(len(df))
        
        for col,asc in zip(cols,ascs):
            if col==0:
                columns=None
            else:
                columns=df.columns[col-1]
            
            # stable sort
            df.sort(columns, ascending=asc, inplace=True, kind='mergesort')
        
        perm = df[cf]
        del df[cf]
        for w in self._filters:
            if w:
                w.reorder(perm)
        try:
            self._query_selected = self._query_selected[perm]
        except TypeError:
            pass
    
    @perr
    def _sort_click(self,col):
        hist = self._sort_history
        if hist:
            (last_col, last_asc) = hist.at(-1)
            # toggle current order, else reapply order
            if last_col==col:
                asc = not last_asc
            else:
                asc = hist.get(col,True)
        else:
            asc = True
        # update history
        hist[col]=asc
        
        # finally sort
        self._sort([col],[asc])
        self._update()
    
    @perr
    def showHeaderContext(self, pos):
        col = self._table.horizontalHeader().logicalIndexAt(pos)
        if col==0:
            return
        menu = self._filter_menus[col-1]        
        if not menu:
            return
        
        menu.exec_(QCursor.pos())
        self._update()
    
    def _update_selection(self):
        names=['Index']
        
        if self._failing:
            m = True
        else:
            m=self._query_selected
            # if it is a pandas thing, want a boolean copy (numpy complains if trying to & floats and bools together, have to be explicit)
            try:
                m = np.array(m.values,dtype=bool)
            except:
                pass
        
        for w,name in zip(self._filters,self._full_df.columns):
            if w:
                m &= w.selected
                if not np.all(w.selected):
                    names.append(name+' *')
                    continue
            names.append(name)
        
        self._column_names = names
        self._viewed_df = self._full_df[m]
    
    def _update(self):
        #testing:
        if not len(self._full_df.columns): #annoy: not so Pythonic, typical Pandas...
            return
        
        self._update_selection()
        df = self._viewed_df
        table = self._table
        with Widget.signalsBlocked(table):
            #column_names = ['index']+list(df.columns)
            column_names = self._column_names
            ncol = len(column_names)
            nrow = len(df)
            index = df.index
            values = df.values
            
            table.setHorizontalHeaderLabels(column_names)
            table.setRowCount(nrow)
            for row in range(nrow):
                item = QTableWidgetItem(str(index[row]))
                item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                table.setItem(row,0,item)
                for col in range(ncol-1):
                    item = QTableWidgetItem(str(values[row,col]))
                    item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                    table.setItem(row,1+col,item)
        
        #table.resizeColumnsToContents()
        
    @perr
    def sizeHintForColumn(self,i):
        
        #if self._column_size_hints[i]
        fm = self.fontMetrics()
        o = fm.width('mmm') # a hack to avoid obscuring column header when you click on a column (Qt makes it bold, adds a direction arrow... yay)
        # there seriously is no perfect way to get these things sized properly, is there?
        hint = fm.width(str(self._full_df.columns[i]))+o+10
        for v in self._full_df.values[:,i]:
            width = fm.width(str(v))+10
            if width>hint:
                hint=width
        return hint
    def _filter_fail(self):
        if self._failing:
            return
        self._failing = True
        self._query_widget.setStyleSheet('QLineEdit { background: rgb(255,128,128) }')
        self._update()
    def _filter_succeed(self):
        if self._failing:
            self._failing = False
            self._query_widget.setStyleSheet('QLineEdit { background: rgb(255,255,255) }')
        self._update()
    
    @perr
    def _on_filter_changed(self,txt):
        #idea: took me a few minutes to remember that I have that context menu filter thing.  Was annoyed again that I couldn't filter with 'block' in A etc.
        txt=txt.strip()
        if not txt:
            self._query_selected = True
            return self._filter_succeed()
        
        try:
            self._query_selected = self._full_df.eval(txt)
        except:
            return self._filter_fail()
        
        if not isinstance(self._query_selected,pd.Series):
            return self._filter_fail()
        
        self._filter_succeed()



# just some testing code
if __name__ == '__main__':
    if 'mw' in globals():
        #plt.close(mw.fig)
        mw.close()
    
    df=pd.DataFrame.from_csv('/home/Josh/big_table.csv')
    df2 = df.copy()
    df2.correlation*=10
    df2 = df2[~df2.A.str.startswith('rew')]
    
    #mw = DataFrameWidget(df)
    mw = DataFrameWidget()
    
    #mw = ColumnFilterWidget()
    #mw.setValues(df.A.values)

    mw.show()
