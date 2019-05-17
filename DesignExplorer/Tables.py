from __future__ import absolute_import
from .common import *

'''
I was not at all pleased by the tables that Qt offered... so I put this together.
I won't claim it is better, but it works better for what I use it for.
'''






'''
so to do anything even somewhat complicated with a table, I need to do it myself
with a QAbstractTableModel derivation and QTableView and QWidget derivation.
Which means I loose out on the huge number of methods available in QTableWidget,
like setCellWidget, or even just setting the column headers.
'''
# seriously Qt...
def tableCell(table,row,col):
    # in Qt, tables can be either a QTableWidgetItem or an arbitrary widget you placed at this
    # position.  Frustratingly inconsistent interface, this function tries to ame it a bit more
    # consistent...
    ret = table.item(row,col)
    if ret is None:
        ret = table.cellWidget(row,col)
    return ret


def dumpTable(table):
    # a list of dictionaries, item per row and key per column.  For a Qt Table, not sure why this basic functionality is
    # missing...
    data=[]
    for i in range(table.rowCount()):
        data.append([tableCell(table,i,j) for j in range(table.columnCount())])
    return data

def printTable(table):
    print(dumpTable(table))

# doesn't work, QTableWidget demands ownership over applied widgets, will
# delete them whenever it wants too.  Honestly not even sure it if is safe
# to hold a reference for later comparison (needed to find row based on callbacks,
# yet another absurd limitation of Qt...)
'''
def takeCell(table,row,col):
    cell = table.takeItem(row,col)
    if cell is None:
        cell = table.cellWidget(row,col)
        if cell is not None:
            table.removeCellWidget(row,col)
    return cell

def setCell(table,row,col,val):
    if isinstance(val,QWidget):
        table.setCellWidget(row,col,val)
    else:
        table.setItem(row,col,val)
'''


class TableSortableItem(QTableWidgetItem):
    # see MyTableWidget
    def __init__(self,value):
        QTableWidgetItem.__init__(self)
        self.value = value
    def __lt__(self,other):
        return self.value < other.value
    def __repr__(self):
        return 'TableSortableItem({})'.format(self.value)
    __str__=__repr__

class MyTableWidget(QTableWidget):
    # QTableWidget is so utterly disappointing.  This class adds at least somewhat competent
    # support for drag/drop reordering and sorting of tables.  Almost assuredly, you are
    # doing something wrong if you use a QTableWidget over this class?  Unless you fixed the problems
    # better than I have.
    orderChanged = pyqtSignal()
    def orderChangeEvent(self):
        self.orderChanged.emit()
    
    def __init__(self, *args, **kwargs):
        QTableWidget.__init__(self, *args, **kwargs)
        
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.viewport().setAcceptDrops(True)
        self.setDragDropOverwriteMode(False)
        self.setDropIndicatorShown(True)        
        
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        
        self.horizontalHeader().setResizeMode(QHeaderView.ResizeToContents)
        
        ## could do it manually, but I have another QTableWidget thing (DataFrameWidget)
        ## that also needs extra handlers so this allows for more flexible extensions (for now at least).
        #Widget.addHandler(self,'keyPressEvent',tableCopyAllHandler)
    
    def autoSize(self):
        #hack, but seems to work??
        self.setMinimumSize(self.horizontalHeader().length()+60,self.verticalHeader().length()+100)
    '''
    #testing:
    def resizeEvent(self,event):
        tw=event.size().width()
        N = self.columnCount()
        
        wh = 0
        for i in range(N):
            self.sizeHint
        for i in range(N):
            self.setColumnWidth(i, tw/N)
    '''
    
    #testing:
    def minimumSizeHint(self):
        hh = self.horizontalHeader()
        vh = self.verticalHeader()
        w=h=0
        
        if vh.isVisible():
            w+=vh.width()
        for i in range(self.columnCount()):
            if not self.isColumnHidden(i):
                #w+=self.columnWidth(i)
                w+=self.sizeHintForColumn(i)
        
        if hh.isVisible():
            h+=hh.height()
        for i in range(self.rowCount()):
            if not self.isRowHidden(i):
                h+=self.rowHeight(i)+4
                #h+=self.sizeHintForRow(i)+1
        
        w = self.size().width()
        #dout(w,h)
        return QSize(w,h+10)
    '''
    def sizeHintForColumn(self,c):
        fm = self.fontMetrics()
        max_w = 0
        for i in range(self.rowCount()):
            w=fm.width(self.item(i,c).text())+10
            if w>max_w:
                max_w=w
        return max_w
    '''
    '''
    @perr
    def sizeHintforColumn(self,ci):
        width=0
        options = self.viewOptions()
        for ri in range(self.rowCount()):
            index=self.model().index(ri,ci)
            
            widget = self.cellWidget(ri,ci)
            delegate = self.itemDelegate(index)
            
            if widget and widget.sizeHint().width()>width:
                width = widget.sizeHint().width()
            w = delegate.sizeHint(options,index).width()
            if w>width:
                width = w
        return w+1
    '''     
            
            
            
    # good job Qt, have to make fake rows and fake items just to do something as simple as reordering the rows...
    def reorder(self,order):
        # imagine adding a new column with the 'order' values.  then sort by that column.
        # actually, that's exactly what happens.  Signals are bloked but otherwise exactly how this method is implemented.
        with Widget.signalsBlocked(self):
            c=self.columnCount()
            self.insertColumn(c)
            for i,row in enumerate(order):
                self.setItem(row,c,TableSortableItem(i))
            self.sortByColumn(c,Qt.AscendingOrder)
            self.removeColumn(c)
        
        self.orderChangeEvent()
                
    @perr
    def dropEvent(self, event):
        if event.source() == self and (event.dropAction() == Qt.MoveAction or self.dragDropMode() == QAbstractItemView.InternalMove):
            success, target_row, target_col, topIndex = self.dropOn(event)
            if success:             
                selRows = self.getSelectedRowsFast()                        
                if selRows:
                    nrow = self.rowCount()
                    ncol = self.columnCount()
                    
                    if target_row==-1:
                        target_row=nrow
                        insert_i=nrow-1
                    
                    rows=[]
                    sel_rows=[]
                    for row in range(nrow):
                        if row in selRows:
                            sel_rows.append(row)
                        else:
                            rows.append(row)
                        
                        if row==target_row:
                            insert_i = len(rows)-1
                    #fixme: I think this fails if there are hidden rows.
                    rows = rows[:insert_i]+sel_rows+rows[insert_i:]                    
                    self.reorder(rows)
                #event.accept()
                return
        else:
            # else let the default happen
            QTableWidget.dropEvent(event)
        return

    def getSelectedRowsFast(self):
        #style: most of these methods are internal...  should rename them.
        # for the most part, this class is only here to allow manual and programatic
        # reordering (a feature that surely should have been provided by Qt, seriously
        # how are the built-in tables not reorderable by the user or programatically!?)
        return list(set(index.row() for index in self.selectedIndexes()))
        '''
        selRows = []
        for item in self.selectedItems():
            if item.row() not in selRows:
                selRows.append(item.row())
        return selRows
        '''

    def droppingOnItself(self, event, index):
        dropAction = event.dropAction()

        if self.dragDropMode() == QAbstractItemView.InternalMove:
            dropAction = Qt.MoveAction

        if event.source() == self and event.possibleActions() & Qt.MoveAction and dropAction == Qt.MoveAction:
            selectedIndexes = self.selectedIndexes()
            child = index
            while child.isValid() and child != self.rootIndex():
                if child in selectedIndexes:
                    return True
                child = child.parent()

        return False

    def dropOn(self, event):
        if event.isAccepted():
            return False, None, None, None

        index = QModelIndex()
        row = -1
        col = -1

        if self.viewport().rect().contains(event.pos()):
            index = self.indexAt(event.pos())
            if not index.isValid() or not self.visualRect(index).contains(event.pos()):
                index = self.rootIndex()

        if self.model().supportedDropActions() & event.dropAction():
            if index != self.rootIndex():
                dropIndicatorPosition = self.position(event.pos(), self.visualRect(index), index)

                if dropIndicatorPosition == QAbstractItemView.AboveItem:
                    row = index.row()
                    col = index.column()
                    # index = index.parent()
                elif dropIndicatorPosition == QAbstractItemView.BelowItem:
                    row = index.row() + 1
                    col = index.column()
                    # index = index.parent()
                else:
                    row = index.row()
                    col = index.column()

            if not self.droppingOnItself(event, index):
                # print 'row is %d'%row
                # print 'col is %d'%col
                return True, row, col, index

        return False, None, None, None

    def position(self, pos, rect, index):
        r = QAbstractItemView.OnViewport
        margin = 2
        if pos.y() - rect.top() < margin:
            r = QAbstractItemView.AboveItem
        elif rect.bottom() - pos.y() < margin:
            r = QAbstractItemView.BelowItem 
        elif rect.contains(pos, True):
            r = QAbstractItemView.OnItem

        if r == QAbstractItemView.OnItem and not (self.model().flags(index) & Qt.ItemIsDropEnabled):
            r = QAbstractItemView.AboveItem if pos.y() < rect.center().y() else QAbstractItemView.BelowItem

        return r
        
        
        

class Row(object):
    '''
    perhaps misguided?  This class reprents a row in a Table object.  Attempts
    to apply the data representation style of other qt widgets (in which the visual
    representation is tied to the underlying data...  a checkbox is a visual representation
    and user interface for controlling a boolean value.)
    
    The Table class I made endeavours to represent a sequence of rows.  Let the user
    modify these values, interrogate the widget for a list of dictinoaries describing the
    values.
    
    If I had to do this again, I'd surely separate teh column names from the return values.
    Table.data would be a matrix, users could ask for the column/row labels separately.  Better
    than explicit dictinoaries.  But in any case, this is far more useful than the tables provided by default for Qt.
    
    '''
    class BuildingContext(object):
        def __init__(self,row, row_index):
            self.row_index=row_index
            self.row=row
        def __enter__(self):
            return self
        def __exit__(self,e_ty,e_val,tb):
            #testing:
            #self.row.table.resizeColumnsToContents()
            
            self.row.table.tableDataChangedEvent()
            delattr(self.row,'build') # one time use
        
        def __call__(self, name, w=None,**kwargs):
            kwargs.setdefault('store',True)
            with Widget.signalsBlocked(self.row.table):
                row = self.row_index
                col = self.row.col_names.index(name)
                
                if w is None:
                    w=QTableWidgetItem()
                    self.row.table.setItem(row,col,w)
                else:
                    # this keeps the cell widgets from doing stupid things with focus
                    # such as all button types linking up and causing arrow keys and tabs
                    # to cycle between only them rather than sanely navigating the table.
                    if isinstance(w,(QAbstractButton,QCheckBox)):
                        w.setFocusPolicy(Qt.NoFocus)
                    self.row.table.setCellWidget(row,col,w)
                    if kwargs.get('cb',None) is None:
                        kwargs['cb']=self.row._on_change
                
                giz = Gizmo(name,w=w,**kwargs)
                self.row.gizmos.append(giz)
            return giz
    
    def __init__(self,table):
        row = table.rowCount()
        table.insertRow(row)
        self.table=table
        self.gizmos=[]
        self.build=self.BuildingContext(self, row)
        
        self._xb = self.build('remove',QPushButton(), cb=self._on_remove, val='X',store=False)
        self._xb.widget.setToolTip('Remove row')
        appendStyleSheet(self._xb.widget,'''
            QPushButton{
                font: bold 10px;
                background-color: #cccccc;
                width: 20px;
                max-height:12px;
                border-radius: 3px;
                border: 1px solid #000000;
                margin-top: 6px;
                margin-bottom: 5px;
                margin-left: 12px;
                margin-right: 12px;
                padding: 2px;
            }
            QPushButton:pressed {
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #999999, stop:1 #a6a6a6)
            }
        ''')
        self._xb.widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self._cb = self.build('copy',QPushButton(), cb=self._on_copy, val='*',store=False)
        self._cb.widget.setToolTip('Copy row')
        appendStyleSheet(self._cb.widget,'''
            QPushButton{
                font: normal 10px;
                background-color: #cccccc;
                width: 20px;
                max-height:12px;
                border-radius: 3px;
                border: 1px solid #000000;
                margin-top: 6px;
                margin-bottom: 5px;
                margin-left: 12px;
                margin-right: 12px;
                padding: 2px;
                padding-top: 4px;
            }
            QPushButton:pressed {
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #999999, stop:1 #a6a6a6)
            }
        ''')
        self._cb.widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    
    def __getitem__(self,name):
        return self.gizmos[self.col_names.index(name)]
    
    def get_index(self):
        for i in range(self.table.rowCount()):
            xb = tableCell(self.table,i,0)
            if self._xb.widget == xb:
                return i   
    @perr
    def _on_copy(self,*args):
        row = self.table.add()
        row.set_data(self.data())
    
    @perr
    def _on_remove(self,*args):
        self.table.removeRow(self.get_index()) # does this not trigger changes??
        
        # testing:
        #self.table.resizeColumnsToContents()
        
        self.table.remove(self)
    
    #fixme: resizeCols... won't always be triggered.  I don't have all the widgets passing through these callbacks.
    # need to implement a separate callback system for resizeing and such...  then add in table.autoSize()
    @perr
    def _on_change(self,*args):
        #print(self.get_index(),'widget changed callback')
    
        #testing:
        #self.table.resizeColumnsToContents()
        
        self.table.tableDataChangedEvent()
    
    def set_data(self,data):
        N=0
        for giz in self.gizmos:
            if giz.name in data:
                N+=1
                giz.value = data[giz.name]
        
        if N!=len(data):
            invalid = list(set(data.keys()) - set(self.col_names))
            raise KeyError('the following invalid columns were specified: {}'.format(invalid))
        
        self._on_change()
    
    def data(self):
        return {giz.name:giz.value for giz in self.gizmos if giz.store}
        
        



class Table(MyTableWidget):
    '''
    An early attempt to fix all the problems/limitations with the table classes provided by Qt.
    
    For better or worse, this widget acts more like other widgets...  It acts as a proxy
    for some underyling data.  Currently, this is a list of dictionaries (one list item per row,
    dictonary keys are the columns).  Could be better... but this is what I have for now.
    
    Just like a checkbox typically acts as a proxy for some boolean value, a Table widget is a proxy for a list of dictionaries
    all with the same keys.
    
    Exceptionally convenient if the column names are exactly what you want.
    '''
    
    #idea: a rather poor choice to force column names to match what is returned via the
    # data() method.  surely more optimal and flexible to store all the values in arrays (lke a pandas.DataFrame).
    # and go from there.
    
    # annoyingly long name because dataChangedEvent and changeEvent etc were already taken...
    # and QTableWidget's changeEvent is more general -- trigers on way more than I want (like addWidget(table))
    tableDataChanged = pyqtSignal()
    def tableDataChangedEvent(self,event=None):
        self.tableDataChanged.emit()
    
    def __init__(self,parent, row_type, editable=None):
        self.row_type=row_type
        self.rows=[]        
        names=row_type.col_names
        MyTableWidget.__init__(self,0,len(names),parent)
        self.setHorizontalHeaderLabels(names)
        self.resizeColumnsToContents()
        self.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
        
        connect(self.itemChanged,self.tableDataChangedEvent)
        
        if not editable:
            editable = [True]*len(names)
        self._column_editable = editable            
        
        #clean: for backwards compatibility
        self.table=self

        appendStyleSheet(self,'''
            QWidget {
                background: #ECECEC;
            }
            QLineEdit {
                background: #ffffff;
            }
            QTableWidget {
                background: #ffffff;
                border: 1px solid black;
            }
        ''')
    
    @perr
    def add(self,*args):
        row = self.row_type(self)
        self.rows.append(row)
        
        rowi=len(self.rows)-1
        for coli,editable in enumerate(self._column_editable):
            if not editable:
                item = self.item(rowi,coli)
                item.setFlags(item.flags() ^ (Qt.ItemIsEditable | Qt.ItemIsEnabled))
        '''
        for giz,editable in zip(row.gizmos,self._column_editable):
            if not editable:
                giz.widget.setFlags(giz.widget.flags() ^ Qt.ItemIsEditable)
                print('WEYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY')
                giz.value = 'NONONONON'
        '''
        return row
    @perr
    def remove(self,row):
        self.rows.remove(row)
        self.tableDataChangedEvent()
        
    def data(self):
        ret=[None]*len(self.rows)
        for row in self.rows:
            ret[row.get_index()] = row.data()
        return ret
    
    def clear(self):
        self.rows=[]
        self.setRowCount(0)
    
    #def minimumSizeHint(self):
        
    
    #def setEditableColumn(self,column_index, is_editable):
    #    self._column_editable[column_index]=is_editable


