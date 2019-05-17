from __future__ import absolute_import
from .common import *
from .Bases import *
from .DesignMode import DesignMode
from .VisualizeMode import VisualizeMode
from .SimulateMode import SimulateMode
from .version import *

from collections import defaultdict, Counter


project_load_error='''Something seems wrong with the project save data, specifically the designs.
failed to load: {}

could not locate: {}

found data for but was not requested: {}
'''


class CloseSignalingWidget(QWidget):
    # silly simple version of QWidget that bothers to notify interested
    # parties when it is closed.
    closed = pyqtSignal(QCloseEvent)
    def closeEvent(self,event):
        self.closed.emit(event)

class TabBar(QTabBar):
    '''
    A QTabBar that is more convenient for this project.  Allows for searching,
    hiding tabs, reordering tabs, per-tab + global context menu, etc.
    
    Assumes that the tab names will be unique always.
    '''
    tabContextMenuRequested = pyqtSignal(int,QPoint)
    '''
    def tabSizeHint(self,i):
        if not self.isTabVisible(i):
            return QSize(1,1)
        else:
            return QTabBar.tabSizeHint(self,i)
    '''
    def tabContextMenuRequestEvent(self,index,pos):
        self.tabContextMenuRequested.emit(index,pos)
    def __init__(self,*args,**kwargs):
        QTabBar.__init__(self,*args,**kwargs)
        #self.setMinimumHeight(40)
        self.setExpanding(False)
        #appendStyleSheet(self,'''
        #QTabBar::tab:disabled, QPushButton:disabled { width: 0; height: 0; margin: 0; padding: 0; border: none; min-width: 0; }
        #''')
        appendStyleSheet(self,'''
            .QTabBar::tab:disabled {
                width: 0; height: 0; margin: 0; padding: 0; border: none; min-width: 0;
                }
        ''')

        '''
        #annoy: QTabBar tab customizations
        
        QTabBar tabs aren't actually QObjects or QWidgets.  QTabBar stores a limited set of details per tab and controls
        all access to those properties.  So you can't add a custom dynamic property to a single tab.  This is why the solution
        used currently for hiding tabs hijacked the 'disabled' property.
        
        Would have to reimplement the paint method (or possibly initStyleOption?  that seems more dangerous and more difficult).  Which
        would be quite annoying and not ideal... might be worth inheriting in C++ and building a custom type, however that is done.        
        '''
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        connect(self.customContextMenuRequested,self._onCustomContextMenuRequested)
    def _onCustomContextMenuRequested(self,p):
        index = self.tabAt(p)
        p = self.mapToGlobal(p)
        self.tabContextMenuRequestEvent(index,p)
    
    def data(self):
        # a list of tabData for all tabs in order (including hidden tabs)
        return [self.tabData(i) for i in range(self.count())]
    
    def setTabButton(self,i,pos,b):
        # puts a button on the tab, right side.
        QTabBar.setTabButton(self,i,pos,b)
        b.setEnabled(self.isTabVisible(i))
        b.setToolTip('Click to optimize design')
        appendStyleSheet(b,'''
            .QPushButton {
                max-width: 30px; 
                max-height: 20px; 
                border: 1px solid #000000; 
                border-radius: 4px; 
                border-style: outset;
            }
            .QPushButton::pressed {
                background-color: #b32d00
            }
        ''')

    def setTabVisible(self,i,visible=True):
        # show/hide a tab
        QTabBar.setTabEnabled(self,i,visible)
        
        for pos in (0,1):
            b = self.tabButton(i,pos)
            if b:
                b.setVisible(visible)
        
        self.adjustSize()
    def showAllTabs(self):
        for i in range(self.count()):
            self.setTabVisible(i,True)
    def isTabVisible(self,i):
        return QTabBar.isTabEnabled(self,i)
    def showOnlyTabs(self,which):
        # hide all tabs except those specified in the sequence 'which'
        for i in range(self.count()):
            self.setTabVisible(i,i in which)
    
    def rename(self,old_name,new_name):
        # change the name of of a tab
        i = self.names().index(old_name)
        self.setTabText(i,new_name)
    
    def index(self,name):
        # search for a tab with given name (else raises a ValueError)
        for i in range(self.count()):
            if self.tabText(i)==name:
                return i
        raise ValueError("{} is not a tab here".format(name))
    
    def names(self):
        # list of tab names as they appear to the user
        return [self.tabText(i) for i in range(self.count())]
    def tabOrder(self):
        # list of tab names as they appear to the user
        return self.names()
    def setTabOrder(self,new_order):
        '''
        provide a list of tab names (or indices if you must) to be used as the new ordering.  Assumes that tab
        names are unique!
        
        '''
        N = self.count()
        if len(new_order) != N:
            raise ValueError("length of new order doesn't match number of tabs")
        
        if not new_order:
            return
        
        #annoy: only way to reorder tabs is via moveTab, which is actually doing inserts
        # so just easier to get all the names up front and look up every time.  inefficient... but shouldn't
        # actually matter in practice.
        new_order = list(new_order)
        for i in range(N):
            if isinstance(new_order[i],int):
                new_order[i] = self.tabText(new_order[i])
        
        if len(set(new_order)) != len(new_order):
            raise NotImplementedError("currently, the tab names must be unique for setTabOrder to function")
        
        for dst,name in enumerate(new_order):
            src = self.index(name)
            self.moveTab(src,dst)
        
class DesignListDialog(BetterDialog):
    '''
    Displays all the Designs and lets users apply certain operations to all of the Designs
    that they select in the list.  Also checkboxes to change if the Designs are selected
    (in terms of which Designs are Visualized).
    '''
    def __init__(self,main):
        BetterDialog.__init__(self)
        self._main = main
        
        self._lw = QListWidget(self)
        self._lw.setSelectionMode(QAbstractItemView.ExtendedSelection)
        # no interest in adding support for reordering
        
        self._relist()
        connect(self._lw.itemChanged,self._onItemChanged)
        
        buts = QHBoxLayout()
        lay = QVBoxLayout()
        
        def add(name,fn):
            b = QPushButton(name)
            buts.addWidget(b)
            connect(b.pressed,fn)
        add('Export',self._export)
        add('Delete',self._delete)
        
        #fixme: selection system is unintuitive.  No indicator on tab bar if a design is 'selected', and conflicts with terminology
        # especially confusing in this list view... User will wonder if the checked designs are what get exported...
        txt = QLabel("Use checkboxes to select designs for 'only selected' visualizations and such.\nHighlight one or more designs to use the buttons below.")
        
        lay.addWidget(self._lw)
        lay.addWidget(txt)
        lay.addLayout(buts)
        self.setLayout(lay)
        
    def _relist(self):
        lw = self._lw
        main = self._main
        
        lw.clear()
        for d in main.designs():
            item = QListWidgetItem(d.name,lw)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked if d.selected else Qt.Unchecked)
    
    def _onItemChanged(self,item):
        row = self._lw.row(item)
        new_name = item.text()
        design = self._main.designs()[row]
        old_name = design.name
        
        design.name = new_name
        design.selected = (item.checkState()==Qt.Checked)

    def _selCheck(self):
        if not len(self._lw.selectedItems()):
            QMessageBox.critical(None,'Nothing To Do','Highlight one or more designs first')
            return False
        return True
    
    @property
    def _sel(self):
        ds = self._main.designs()
        ret=[ds[self._lw.row(item)] for item in self._lw.selectedItems()]
        return ret
    
    def _export(self):
        if not self._selCheck():
            return
        
        parent_folder = QFileDialog.getExistingDirectory(None,'Choose Export Folder')
        if not parent_folder:
            return
        
        #idea: option to export to separate folders, rather than only prefixed?
        #idea: merge the exports for just one overwrite check?  very annoying that qt doesn't appear to provide
        # GUIs for file operations.
        for design in self._sel:
            design.export(parent_folder,interactive=True)
    
    def _delete(self):
        if not self._selCheck():
            return
        
        #names = human_list([d.name for d in self._sel])
        msg = "Warning", "Are you sure you want to delete the {} selected designs?".format(len(self._sel))
        res = QMessageBox.question(self,msg,QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if res == QMessageBox.No:
            return
        
        for d in self._sel:
            d.remove()
        self._relist()

        
def human_list(items,quoted=False):
    '''
    make a comma separated string of the given items.  just 2 items
    will be separated by 'and' with no commas.  If more than 2 items, 
    final and will be preceded by a comma.  items are converted to strings.
    optionally items can be quoted (single guotes).
    
    pretty convenient!
    '''
    items = [str(item) for item in items]
    if quoted:
        items=["'"+item+"'" for item in items]
    
    N=len(items)
    if N==0:
        return ''
    if N==1:
        return items[0]
    if N==2:
        return items[0]+' and '+items[1]
    items[-1]='and '+items[-1]
    return ', '.join(items)

class MainDesignTabContextMenu(QMenu):
    '''
    The context menu that appears either for a specific design tab or when the user
    right clicks the tab bar itself.  This is the main way users have to add/remove/rename
    designs via the tab bar.
    '''
    def __init__(self,main,design):
        QMenu.__init__(self)
        self._main = main
        
        def a(*labels):
            def helper(label):
                act = self.addAction(label)
                attr = '_'+'_'.join(label.lower().split(' '))
                fn = getattr(self,attr)
                connect(act.triggered,lambda *unused: fn())                
            for label in labels:
                helper(label)

        
        if not design:
            a('New', 'List View')
        else:
            self._design = design
            a('Rename','Copy','Delete','Optimize','Export')
    
    def _uniqueName(self,base):
        name = base
        names = [d.name for d in self._main.designs()]
        
        i=2
        while name in names:
            name = '{} ({})'.format(base,i)
            i+=1
        return name
    def _name(self,title, default_name=""):
        text,ok = QInputDialog.getText(self,title,"Name:", text=default_name)
        text=text.strip()
        if ok:
            #idea: attach validator? to the dialogbox? can it change color?
            # http://snorf.net/blog/2014/08/09/validating-user-input-in-pyqt4-using-qvalidator/ ?
            for d in self._main.designs():
                if d.name==text:
                    return None
            # currently no need to validate further.  names are just for the user, doesn't
            # have to be a valid file name or anything.
            return text
    
    def _list_view(self):
        d = DesignListDialog(self._main)
        d.exec_()
        
    def _new(self):
        name = self._name('New Design', self._uniqueName('unnamed'))
        if name:
            self._main.addDesign(name)
    def _rename(self):
        name = self._name('Rename Design',self._design.name)
        if name:
            self._design.name = name
    def _copy(self):
        name = self._name('New Name', self._uniqueName(self._design.name))
        if name:
            self._main.addDesign(name, self._design)
    def _delete(self):
        self._design.remove()
    def _optimize(self):
        self._design.optimize()
    def _export(self):
        self._design.export(interactive=True)

        

class Main(object):
    '''
    This is the object that manages the main GUI for the user.  It represents a single project
    comprised of multiple designs.  Only one Main instance may exist per project (enforced by
    file locks).
    
    Pretty much every action that the user makes or that DesignExplorer code may trigger
    goes through Main.  This is the second most important class, right after Design.  and
    Design can not exist independantly of Main, so...
    '''
    
    
    def _designTabContextMenuShow(self,i,pos):
        if i==-1:
            design = None
        else:
            name = self.design_tabs.tabText(i)
            design = self.findDesign(name)
        self.showDesignTabContextMenu(design,pos)
    
    def showDesignTabContextMenu(self,design,pos):
        MainDesignTabContextMenu(self,design).exec_(pos)
    
    def __init__(self, app_folder, project_folder, project_folder_lock):        
        '''
        Multiple instances may share an application folder (currently unused).  Only one instance
        may have a project folder, thus why a folder lock is required.  see the start function.
        
        '''
        dout('================================ Main init ===============================')
        
        decon_path = os.path.join(os.path.join(app_folder,'bin'),'3dDeconvolve')
        if os.path.exists(decon_path):
            setDeconPath(decon_path)
            #assume this is a user with a working setup?
            #impl: will need some way to get any error messages they encounter
            # back to the devs.  Perhaps add log files to dout as well?
            self._auto_close_dout = True
            #dout.close()
        else:
            dout("WARNING: did not find 3dDeconvolve in app folder, assuming it exists in the user's path already.")
            self._auto_close_dout = False

        self._app_folder = app_folder
        self._project_folder = project_folder
        self._project_folder_lock = project_folder_lock
        self._temp_folder = jk.mkdir(os.path.join(project_folder,'.tmp/'))
        self._project_settings_path = os.path.join(project_folder,'project.pickle')
        self._designs_folder = jk.mkdir(os.path.join(project_folder,'designs/'))
        if os.path.isdir(os.path.join(os.path.expanduser('~'),'.DesignExplorer/bin/images')):
            self._images_folder = os.path.join(os.path.expanduser('~'),'.DesignExplorer/bin/images')
        else:
            self._images_folder = os.getcwd()+'/images'

        self._closed = True
        self._focused_design = None
        self.visualizations = []
        self.default_options = {}
        self.mode = None
        
        self.window = win = CloseSignalingWidget()
        connect(win.closed,self.close)
        appendStyleSheet(self.window,'''
                QWidget {
                    background-color:#dcdcdc;
                    }
                QToolTip {
                    background-color: #f5f5dc;
                    font-size: 12px;
                    font-style: bold;
                    color: black;
                    padding: 1px;
                    border: 1px solid black;
                }
        ''')
        self.window.setContentsMargins(-5,-5,-5,-5)
        self.status = QTextEdit()
        self.status.hide()
        
        #style:  should probably be using underscores for most of this stuff
        self.mode_tabs = QTabBar()
        self.design_tabs = TabBar()
        
        # add new design button
        nbut = QPushButton()
        appendStyleSheet(nbut,'''
            .QPushButton {
                border: 0;
                border-style: outset;
                background-color: #ECECEC;
                }
            .QPushButton::pressed {
                background-color: #f2f2f2;
                border: 2px solid #000000;
                border-radius: 6px;
                }
        ''')
        nicn = QIcon()
        nicn.addPixmap(QPixmap(self._images_folder+'/new.png'))
        nbut.setIcon(nicn)
        nbut.setIconSize(QtCore.QSize(35,35))
        nbut.setToolTip('Create new design variant')
        # fix-DM: for some reason when adding a new design, odd colored borders appear below the new design's tab.
        # this is not the case when starting the program new. There is something about applying the global
        # styles that covers this up.

        self.mode_tabs.setTabsClosable(False)
        self.mode_tabs.setMovable(False)
        appendStyleSheet(self.mode_tabs,'''
            QTabBar {
                border-bottom: 1px solid #000000;
                qproperty-drawBase: 0;
                width: 1000px;
                }
            QTabBar::tab {
                background: #ECECEC;
                border: 1px solid #000000;
                border-bottom: 0;
                border-top-right-radius: 10px;
                border-top-left-radius: 10px;
                min-height: 35px;
                font-size: 20pt;
                }
            QTabBar::tab:!selected {
                background: #cccccc;
                margin-top: 8px;
                border-bottom: 1px solid #666666;
                color: #999999;
                }
            QTabBar::tab:selected {
                margin-left: -6px;
                margin-right: -6px;
                }
            QTabBar::tab:first:selected {
                margin-left: 0;
                }
            QTabBar::tab:first:!selected {
                margin-right: -4px;
                }
            QTabBar::tab:last:selected {
                margin-right: 0;
                }
            QTabBar::tab:last:!selected {
                margin-left: -4px;
                }
        ''')
        m = 0
        for Mode in Main.available_modes:
            self.mode_tabs.addTab(Mode.title)
            self.mode_tabs.setTabToolTip(m,Mode.toolTip)
            m+=1

        connect(self.design_tabs.tabContextMenuRequested,self._designTabContextMenuShow)
        self.design_tabs.setTabsClosable(False)
        self.design_tabs.setMovable(True)
        self.design_tabs.setToolTip('Right click for design options')
        appendStyleSheet(self.design_tabs,'''
            QTabBar {
                 qproperty-drawBase: 0;
            }
            QTabBar::tab {
                background: #E7E7E7;
                border-top: 1px solid #000000;
                border-bottom: 1px solid #000000;
                border-left: 1px solid #000000;
                border-right: 0;
                padding: 4px;
                min-width: 150px;
                min-height: 20px;
            }
            QTabBar::tab:last {
                border-right: 1px solid #000000;;
            }
            QTabBar::tab:!selected {
                background: #cccccc;
                color: #999999;
            }
            QTabBar::tab:only-one {
                border-right: 1px solid #000000;
            }
        ''')

        self.dock = DockArea()
        self.dock_scroll = sa = QScrollArea()
        sa.setWidget(self.dock)
        sa.setWidgetResizable(True)
        #sa.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        appendStyleSheet(sa,'''
            .QScrollArea {
                border: 1px solid black;
            }
        ''')

        tabw = QVBoxLayout()
        tabw.addWidget(self.mode_tabs)

        dtab = QHBoxLayout()
        dtab.addWidget(self.design_tabs)
        dtab.addStretch()
        dtab.addWidget(nbut)
        #dtab.setContentsMargins(0,0,0,0)

        top = QVBoxLayout()
        top.addLayout(dtab)
        self.mode_widget_holder = QPlaceholder()
        top.addLayout(self.mode_widget_holder)
        top_widget = QWidget()
        top_widget.setLayout(top)
        appendStyleSheet(top_widget,'''
            .QWidget{
                background-color:#ECECEC; 
                margin-top: -10px;
                border-left: 1px solid black;
                border-right: 1px solid black;
                border-bottom: 1px solid black;
            }
        ''')

        splitter = QSplitter()
        splitter.setOrientation(Qt.Vertical)
        appendStyleSheet(splitter,'''
            QSplitter::handle {
                background: #dcdcdc;
                height: 10px;
                }
        ''')
        splitter.addWidget(top_widget)
        splitter.addWidget(self.status)
        splitter.addWidget(self.dock_scroll)

        lay = QVBoxLayout()
        lay.addLayout(tabw)
        lay.addWidget(splitter)
        lay.setSpacing(0)
        
        #fixme: remove when done
        self.splitter = splitter
        #fixme: make the splitter do reasonable proportions.  
        #why didn't these help initial layout?
        #self.status.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        #self.dock_scroll.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
        #and can't resize here, splitter hijacks it all
        # I hate this splitter
        #splitter.setStretchFactor(0,1000)
        #splitter.setStretchFactor(1,0)
        #splitter.setStretchFactor(2,1000)
        
        #but = QPushButton()
        #but.setText('update')
        #but.clicked.connect(self.update_test)
        #lay.addWidget(but)      
        connect(nbut.clicked, lambda unused: self._new())
        connect(self.design_tabs.currentChanged,self._onDesignTabChange)
        connect(self.mode_tabs.currentChanged,self._setMode)
        
        self._load()
        self._closed = False
        self._setMode(0)
        win.setLayout(lay)
        screenShow(win,2,full=False)
        #win.show()
        win.raise_()
        win.activateWindow()
        dout('================================ Main init finished ===============================')
    #################################################################################################################
    ## serialization stuff, disk access
    # note that most of it is private.  a Main instance only ever has to load the project once,
    # as it is not supported to change projects afterwards. 
    _serialization_version = 0
    
    def _readSettings(self):
        path = self._project_settings_path
        if os.path.exists(path) and not DEV_IGNORE_EXISTING:
            with open(path,'rb') as f:
                return pickle.load(f)
        else:
            return dict(project_name = None,designs = [], focused_design=None, default_options={}, version=self._serialization_version)
    def _writeSettings(self):
        settings = dict(project_name = self._project_name,default_options=self.default_options,focused_design=None,version=self._serialization_version)
        settings['designs'] = [d.name for d in self.designs()]
        if self._focused_design:
            settings['focused_design'] = self._focused_design.name
        
        with open(self._project_settings_path,'wb') as f:
            pickle.dump(settings,f,protocol=2)
        return settings
    
    @perr
    def _save(self):
        dout('saving project settings')
        self._writeSettings()
    @perr
    def save(self):
        # save all designs as well as project-wide settings
        dout('saving designs')
        for d in self.designs():
            d.save()
        self._save()
    
    def _newdlg(self,title,text,default_name):
        dlg = QInputDialog()
        dlg.setInputMode(QInputDialog.TextInput)
        dlg.setTextValue(default_name)
        dlg.setLabelText(text)
        dlg.setWindowTitle(title)
        dlg.resize(100,400) 
        appendStyleSheet(dlg,'''
            .QLineEdit {
                background: #ffffff;
                border: 1px solid #000000;
            }
            .QPushButton {
                background-color: #cccccc;
                font: normal 12px;
                border-style: outset;
                border-width: 1px;
                border-radius: 6px;
                border-color: black;
                width: 50px;
                height: 12px;
                padding: 4px;
                margin: 6px;
            }
            .QPushButton:pressed {
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #999999, stop:1 #a6a6a6)
            }
            QWidget {
                border: 0px;
            }
        ''')                           
        ok = dlg.exec_()                                
        name = dlg.textValue()
        return(name,ok)

    def _setProjectName(self,name,loading=False):
        if not name:
            default_project_name = 'unnamed'
            name,ok=self._newdlg('New Project!','Enter project name:',default_project_name)
            #idea: need a custom QDialog if I want to hide the cancel button...
            if not ok:
                name = default_project_name
            name = name.strip()
        
        self._project_name = name
        self.window.setWindowTitle('Design Explorer - '+name)
        if not loading:
            self._save()
    @perr
    def _load(self):
        self._clearTemp()
        
        settings = self._readSettings()
        
        if self._serialization_version != settings['version']:
            pass
        
        self._setProjectName(settings.get('project_name'), loading=True)
        
        
        available_folders = next(os.walk(self._designs_folder))[1]
        design_names = settings['designs']
        assert(len(design_names)==len(set(design_names)))
        designs=[None]*len(design_names)
        all_designs=[]
        failed=[]
        missing=[]
        extra=[]
        
        for folder in available_folders:
            folder = os.path.join(self._designs_folder,folder)
            with StatusCatch() as err:
                d = Design(self,folder)
            if err:
                failed.append((folder,err))
                continue
            
            all_designs.append(d)
            
            try:
                i = design_names.index(d.name)
                designs[i] = d
            except:
                extra.append(d)
        
        for name,d in zip(design_names,designs):
            if d is None:
                missing.append(name)
        
        if failed or missing or extra:
            msg = project_load_error.format(failed,missing,extra)
            if not DEV_IGNORE_LOAD_ERRORS:
                raise Exception(msg)
            else:
                dout(msg)
                designs = [d for d in designs if d]
                
            
        
        '''
        all_names = [d.name for d in all_designs]
        c = Counter(all_names)
        if len(all_names) != len(c):
            failed.append(('duplicates in saved designs',c))
        '''
        
        for d in designs:
            self._addDesign(d)
        
        d = self.findDesign(settings['focused_design'])
        if not d:
            dout('WARNING could not find the previously focused design "{}"'.format(settings['focused_design']))
        self._focused_design = d
        
        self.default_options = settings['default_options']
        
    def _clearTemp(self):
        import os,shutil # a workaround for if you reload in spyder
        if os.path.isdir(self._temp_folder):
            shutil.rmtree(self._temp_folder,True)
        os.mkdir(self._temp_folder)
    def requestTempFolder(self):
        '''
        Currently it is guaranteed that this folder will exist during this session.
        If DesignExplorer is restarted, expect that the previous temp folder will
        no longer exist.
        '''
        return mkdtemp(dir=self._temp_folder)
    def returnTempFolder(self,folder):
        '''
        be kind and return your temp folder!
        
        But to be safe, all temp folders are deleted next time DesignExplorer
        starts.  
        '''
        if folder:
            assert(self._temp_folder in folder)
            if os.path.isdir(folder):
                shutil.rmtree(folder,True)

    def _makeDesignFolder(self,name):
        current_folders = next(os.walk(self._designs_folder))[1]
        #simple, makes no assumptions about previous naming conventions, tends towards lower numbers even after many modifications...
        N = len(current_folders)
        for i in range(N+1):
            folder=str(i)
            if folder not in current_folders:
                break
        
        folder = os.path.join(self._designs_folder,folder)
        os.mkdir(folder)
        return folder
        
        '''        
        # tries to include the name, but is robust against invalid characters
        # and duplicates.
        
        current_folders = next(os.walk(self._designs_folder))[1]
        folder = 'initially_named_'+name
        
        #try writing a temp file using the name.  if it fails, just
        # fallback to something simpler.
        
        #but I've seen really strange names in linux.  perhaps better
        # to give up on names entirely?
        
        try:
            tpath = os.path.join(self._temp_folder,folder)
            with open(tpath,'w'):
                pass
            os.remove(tpath)
        except:
            folder='messily_named'
        
        if folder in current_folders:
            for i in range(len(current_folders)):
                folder=str(i) #idea: would it be useful to try appending numbers rather than falling all the way back to just numbers?
                if folder not in current_folders:
                    break
        assert(folder not in current_folders)
        
        folder = os.path.join(self._designs_folder,folder)
        os.mkdir(folder)
        return folder
        '''
    
    ####################################################################################################################################
    ## Mode
    def _setMode(self,index):
        (should_abort, remove_design) = self.leavingCurrentDesign()
        if should_abort:
            return
        Mode = Main.available_modes[index]
        
        if self.mode is not None:
            self.mode.close()
        self.closeAllVisualizations()
        self.setStatus("")
        self.resetDesignTabs()
        
        # for some reason, calling setModeWidget twice in a callback freezes the GUI!
        # very mysterious...  so it is the Mode's responsibility to provide a widget.
        #self.setModeWidget(QWidget())
        self.mode = Mode(self)
        
        
        #fixme: placement??
        '''
        when mode=None:
            as long as the broadcast works, great!  could check if mode is None.  
        here - mode will get a notification of removed design before it is fully added.  lame requirement that modes should 
            manually ignore notifications until they are added.
        at end - works if all modes and visualizations don't assume valid designs.  slightly inefficient
        
        best solution would be to silently remove it somehow.
        '''
        #fixme: the remove related methods look a bit odd, should review them and maybe clean them up.
        if remove_design:
            self.removeDesign(remove_design)
        
        self.mode.addedToMain()
    
    available_modes = [DesignMode,VisualizeMode,SimulateMode]    
    
    def setModeWidget(self,w):
        '''
        used by a mode to set a custom widget in the Main GUI.  Currently this
        appears just above the status text box and visualizations (below the design and mode tabs)
        
        be sure to close the previous widget (BaseMode currently does this for you when the Mode is closed,
        but if for some reason you change widgets mid-mode then you have to close the previous widget).
        '''
        
        self.mode_widget_holder.item = w
        return w #convenient
    
    def getMode(self):
        # what is the current mode?
        return self.mode
    
    def modeBroadcast(self,msg,**kwargs):
        # used by the current mode to send special messages to all visualizations
        for v in list(self.visualizations):
            v.onModeMessage(msg,**kwargs)
    
    ########################################################################################################
    def resetDesignTabs(self):
        #idea: could try to use a previous ordering, but that requires some effort.  when to save
        #, what changes to keep, handling add/remove designs, renaming...
        self.design_tabs.showAllTabs()
        
    def focusVisualization(self,v):
        v.focus()
    
    def focusedDesign(self):
        return self._focused_design
    def designs(self):
        return self.design_tabs.data()
    def selectedDesigns(self,ordered=False):
        return [d for d in self.designs() if d.selected]
    
    @perr
    def activateVisualization(self,cls,**kwargs):
        for v in self.visualizations:
            if isinstance(v,cls) and v.matchesActiveState(**kwargs):
                v.focus()
                return v
        v = cls(self,**kwargs)
        self.addVisualization(v)
        
        v.focus()
        return v
    
    def addVisualization(self,v):
        d = v.widget
        self.dock.addDockWidget(Qt.BottomDockWidgetArea,d,Qt.Vertical)
        #self.dock.addDockWidget(Qt.RightDockWidgetArea,d,Qt.Horizontal)
        assert(v not in self.visualizations)
        self.visualizations.append(v)
    @perr
    def onVisualizationClose(self,v):
        '''
        
        '''
        try:
            self.visualizations.remove(v)
        except ValueError:
            pass
        else:
            self.dock.removeDockWidget(v.widget)
    
    def closeAllVisualizations(self):
        for v in list(self.visualizations):
            v.close()
        self.visualizations = []
    
    def close(self,event=None):
        if not self._closed:
            self.save()
            self.closeAllVisualizations()
            self.window.close()
            self._clearTemp()
            self._project_folder_lock.unlock()
            if self._auto_close_dout:
                dout.close()
    
    @perr
    def onDesignChange(self, design):
        for v in list(self.visualizations):
            v.update(design=design)
    
    def getDefaultOptions(self,kind):
        return deepcopy(self.default_options.get(kind,{}))
    def setDefaultOptions(self,kind,options):
        # the copy isn't necessary I think... but may as well be safe!  surely won't be a performance bottleneck.
        self.default_options[kind] = deepcopy(options)
    
    def setStatus(self,txt):
        self.status.setText(txt)
    def appendStatus(self,txt,newline=True):
        new = self.status.toPlainText()
        if newline:
            new+='\n'
        new+=txt
        self.setStatus(new)
    def _designTabButtonClicked(self,design):
        if not design.valid():
            QMessageBox.critical(self.window,"","Design is invalid, please fix it before trying to optimize")
        else:
            self.optimizeDesign(design)
    
    def leavingCurrentDesign(self):
        '''
        Checks if the current design is valid.  if it isn't, check with the user
        if they want to either abort the current operation (and try to fix the design)
        or discard the design.
        
        returns (should_abort,design_to_remove)
        
        if design_to_remove is None, don't remove anything
        '''
        d = self._focused_design
        if d is not None:
            if not d.valid():
                dlg = QWidget()
                appendStyleSheet(dlg,'''
                    .QWidget {
                        background-color: #ECECEC;
                        }
                    .QLabel {
                        font: bold 12px;
                    }
                    .QPushButton:pressed {
                        background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #999999, stop:1 #a6a6a6)
                    }
                    .QPushButton {
                        background-color: #cccccc;
                        font: normal 12px;
                        border-style: outset;
                        border-width: 1px;
                        border-radius: 6px;
                        border-color: black;
                        width: 65px;
                        height: 15px;
                        padding: 5px;
                        margin: 4px;
                    }
                ''')
                r = QMessageBox.question(dlg,"Abandon Design?","The current design is invalid.  If you leave it now without fixing it, it will be removed.  \n\nAbandon this design?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if r == QMessageBox.Yes:
                    dout('abandoning')
                    return (False,d)
                else:
                    return (True,None)
        return (False,None)    
    
    ###############################################################################################################
    ## design message forwarding and related
    def _designBroadcast(self,message_for_broadcast,design,**kwargs):
        attr = 'design'+message_for_broadcast
        #dout('broadcast {} {}',attr,design)
        getattr(self.mode,attr)(design,**kwargs)
        for v in list(self.visualizations):
            getattr(v,attr)(design,**kwargs)
    
    def renameDesign(self,design,name):
        # renames design, may also use design.name = name
        design.name = name
    def designRenamed(self,design,old_name,**kwargs):
        self.design_tabs.rename(old_name,design.name)
        self._designBroadcast('Renamed',design,old_name=old_name,**kwargs)
    
    def removeDesign(self,design):
        # removes design (design.remove() is also OK)
        # will trigger a Focused broadcast first if the design being removed is invalid.
        design.remove()
    
    def designRemoved(self,design,**kwargs):        
        #first ensure this design isn't focused
        if design == self._focused_design:
            for d in self.designs():
                if d!= design:
                    break
            else:
                d = None
            # but don't do the usual validity check (already know that the design is being removed)
            self._focusDesign(d)
        
        i = self.design_tabs.index(design.name)
        self.design_tabs.removeTab(i)
        self._designBroadcast('Removed',design,**kwargs)
        
    
    def _checkOptimization(self,design):
        i = self.design_tabs.index(design.name)
        b = self.design_tabs.tabButton(i,QTabBar.RightSide)
        if design.state == Design.OPTIMIZED:
            v='o'
        elif design.state == Design.TWEAKED:
            v='t'
        else:
            v='u'
        
        b.setProperty("OptState",v)
        b.style().unpolish(b)
        b.ensurePolished()
        #b.setStyleSheet(b.styleSheet())

    def _uniqueName(self,base):
        name = base
        names = [d.name for d in self.designs()]
        i=2
        while name in names:
            name = '{} ({})'.format(base,i)
            i+=1
        return name

    def _name(self,title,default_name=""):
        name,ok=self._newdlg('New Design','Name:',default_name)
        if ok:
            for d in self.designs():
                if d.name==name:
                    return None
            return name

    def _new(self):
        name = self._name('New Design', self._uniqueName('unnamed'))
        if name:
            self.addDesign(name)

    def _addDesign(self,design,emit=False):        
        if design in self.designs():
            raise ValueError("Can't add {} twice.".format(design))
        
        # if there are no other designs, adding this design will trigger
        # designFocused before all the configuration is finished and
        # before designAdded.  So block the signals for a bit, manually
        # do designFocused 
        with signalsBlocked(self.design_tabs):
            i = self.design_tabs.addTab(design.name)
            b = QPushButton()
            b.setStyleSheet('''
            *[OptState = "u"] { background-color: red; }
            *[OptState = "t"] { background-color: yellow; }
            *[OptState = "o"] { background-color: green; }
            ''')
            # todo-DM: change tool tips to reflect optimization state
            connect(b.clicked,lambda *args: self._designTabButtonClicked(design))
            self.design_tabs.setTabButton(i,QTabBar.RightSide,b)
            self.design_tabs.setTabData(i,design)
            self._checkOptimization(design)
        
        # adding a tab to an empty bar gives that tab focus, and if the bar is not empty you cannot have no focus...  setCurrentIndex(-1) does not work.
        # so have to detect and carefully handle this.  signals were blocked, so have to update internal state manually here.  and if emit=True, then
        # instead should notify in a good order.
        # thankfully this "internal state" is just a single attribute.  
        newly_focused = (len(self.designs())==1)
        
        if emit:
            self.designAdded(design)
            self.focusDesign(design)
            if newly_focused:
                self._focusDesign(design)
        elif newly_focused:
            self._focused_design = design

    def addSS(self,exp,opts=None):
        # just an initial test
        #impl: merge with addDesign
        name = exp.ID
        
        if self.findDesign(name):
            raise ValueError('a design named "{}" already exists'.format(name))
        
        folder = self._makeDesignFolder(name)
        design = Design(self, exp=exp, optimization_settings=opts, folder=folder)
        return self._addDesign(design,emit=True)
        
        
    def addDesign(self,name,src=None):
        '''
        adds a new design to the project.  name must be unique.
        
        Optionally you can specify another design to copy from.  src can be a folder, name, or Design.
        '''
        # adds a new design
        # if no other designs exist, will also broadcast Focused message after the Added message
        
        if self.findDesign(name):
            raise ValueError('a design named "{}" already exists'.format(name))
        folder = self._makeDesignFolder(name)
        rename=False
        
        # try:
        #     design = Design(self,exp=exp,optimization_settings=opts)
        # except Exception as e:
        #     raise
            
        
        if src:
            
            #idea: maybe could support StimSim imports?
            # so messy already...  perhaps should be a Design method instead.
            # thus could support loading a StimSim folder?  I still don't know if
            # I want this feature...
            '''
            if isinstance(src,StimSim.Experiment):
                src = src._internal
            if isinstance(src,StimSim.InternalExperiment):
                pass
            '''
            
            # can be Design, name, or folder
            if not isinstance(src,Design):
                src_design = self.findDesign(src)
                if src_design:
                    if os.path.exists(src):
                        raise ValueError('ambiguous source, could be relative folder or design name.  Please use absolute paths for reliability.')
                    src=src_design
            
            # can be a Design or folder
            if isinstance(src,Design):
                if src not in self.designs():
                    raise Exception("where did you get that Design instance??")
                src.saveAs(folder,name)
            else:
                shutil.copytree(src,folder)
                rename = True
            
            # data now in folder, can load
            try:
                design = Design(self,folder)
            except Exception as e:
                if DEV_IGNORE_LOAD_ERRORS:
                    dout('failed to load design {} in folder {}'.format(name,folder))
                    dout(str_err(e))
                    
                    # erase and continue as if it were a new design
                    shutil.rmtree(folder,True)
                    os.mkdir(folder)
                    design = Design(self, folder, name)
        else:
            # brand new design, no state to load
            design = Design(self, folder, name)
        
        # if copying a folder, still have to change the name.  
        if rename:
            design._name = name
        # tempting to save just fresh designs here but...
        # also should consider that loading a design can modify it
        # (for example, version changes).  
        return self._addDesign(design,emit=True)
    
    def designAdded(self,design,**kwargs):
        self._designBroadcast('Added',design,**kwargs)
    
        
    def optimizeDesign(self,design,*args,**kwargs):
        # see design.optimize
        design.optimize(*args,**kwargs)
    def designOptimized(self,design,**kwargs):
        self._checkOptimization(design)
        self._designBroadcast('Optimized',design,**kwargs)
    
    def selectDesign(self,design):
        # see design.selected
        design.selected = True
    def designSelected(self,design,**kwargs):
        self._designBroadcast('Selected',design,**kwargs)
    
    def deselectDesign(self,design):
        # see design.selected
        design.selected = False
    def designDeselected(self,design,**kwargs):
        self._designBroadcast('Deselected',design,**kwargs)
    
    # I think that reconfiguring is broad enough that
    # it doesn't make sense to go through Main.
    #def reconfigureDesign(self,design):
    def designReconfigured(self,design,**kwargs):
        self._checkOptimization(design)
        self._designBroadcast('Reconfigured',design,**kwargs)
    
    
    def invalidateDesign(self,design):
        # see design.invalidate()
        design.invalidate()
    def designInvalidated(self,design,**kwargs):
        self._checkOptimization(design)
        self._designBroadcast('Invalidated',design,**kwargs)
    
    def _focusDesign(self,design):
        self._focused_design = design
        self.designFocused(design)            
    def focusDesign(self,design):
        #see design.focus()
        i = self.designs().index(design)
        self.design_tabs.setCurrentIndex(i) # this triggers _onDesignTabChange.  a bit odd, but works...
    def _onDesignTabChange(self,index):
        if index==-1:
            d = None
            remove_design = False
        else:
            (should_abort, remove_design) = self.leavingCurrentDesign()
            if should_abort:
                return
            d = self.design_tabs.tabData(index)
        self._focusDesign(d)
        if remove_design:
            self.removeDesign(remove_design)
    def designFocused(self,design,**kwargs):
        self._designBroadcast('Focused',design,**kwargs)
    
    def designExtraChanged(self,design,**kwargs):
        self._designBroadcast('ExtraChanged',design,**kwargs)
    
    def designStyleChanged(self,design,**kwargs):
        self._designBroadcast('StyleChanged',design,**kwargs)
    
    def findDesign(self,name):
        try:
            i = self.design_tabs.index(name)
        except ValueError:
            return None
        return self.design_tabs.tabData(i)



class ProjectLauncher(QDialog):
    '''
    A simple GUI for selecting a new or existing project.  Expect changes, this
    is just an initial draft.
    '''
    def __init__(self,app_folder):
        QWidget.__init__(self)
        self._app_folder = app_folder
        #impl: read settings from app folder.  Can inform of existing project names/locations, recent history, perhaps auto-launching preferences...
        self.main = None
        self._version = version
        if os.path.isdir(os.path.join(os.path.expanduser('~'),'.DesignExplorer/bin/images')):
            self._images_folder = os.path.join(os.path.expanduser('~'),'.DesignExplorer/bin/images')
        else:
            self._images_folder = os.getcwd()+'/images'

        self.setFixedSize(450,150)

        self.setWindowTitle('Project Launcher')
        appendStyleSheet(self,'''
            QToolTip {
                background-color: beige;
                font-size: 12px;
                font-style: bold;
                color: black;
                padding: 1px;
                border: 1px solid black;
            }
            QWidget {
                background-color: #ECECEC;
                font-family: SansSerif;
            }
            QPushButton:pressed {
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #999999, stop:1 #a6a6a6)
            }
            QPushButton {
                background-color: #cccccc;
                font: normal 12px;
                border-style: outset;
                border-width: 2px;
                border-radius: 6px;
                border-color: black;
                width: 150px;
                height: 35px;
                padding: 4px
            }
        ''')

        lay = QVBoxLayout()
        
        self.welcome = QLabel('Welcome to the fMRI Design Explorer!\n')
        self.welcome.setAlignment(Qt.AlignCenter)
        appendStyleSheet(self.welcome,'''
            .QLabel {
                font: normal 20px;
                color: black;
            }
        ''')

        self.choose = QLabel('Please choose an option below\n')
        self.choose.setAlignment(Qt.AlignCenter)
        appendStyleSheet(self.choose,'''
            .QLabel {
                font: default 12px;
                color: black;
            }
        ''')
        
        bot = QHBoxLayout()

        b = QPushButton('Create a new\nproject')
        b.setToolTip('Select to create a new project in a user-defined location')
        bot.addWidget(b)
        connect(b.clicked, lambda unused: self._browse())

        b = QPushButton('Load an existing\nproject')
        b.setToolTip('Select to load an existing project from a user-defined location')
        bot.addWidget(b)
        connect(b.clicked, lambda unused: self._browse())

        b = QPushButton('Use the Default\nproject')
        b.setToolTip('Select to use the Default internal project')
        bot.addWidget(b)
        connect(b.clicked, lambda unused: self.launch(app_folder+'default_project/'))
        
        bot.setSpacing(20)

        h = QHBoxLayout()
        hbut = QPushButton('?')
        hbut.setToolTip('Open user manual')
        hbut.setContentsMargins(0,8,0,4)
        connect(hbut.clicked, lambda unused: self.hclick())
        appendStyleSheet(hbut,'''
            .QPushButton:pressed {
                background-color: #66ccff;
            }
            .QPushButton {
                font-style: bold;
                font-size: 10px;
                color: white;
                background-color: #0066ff;
                border-style: outset;
                border: 1px solid #000000;
                padding: 2px;
                width: 20px;
                height: 8px;
                border-radius: 2px;
            }
        ''')

        v = QLabel('version: '+self._version)
        v.setContentsMargins(0,8,0,4)
        v.setAlignment(Qt.AlignLeft)
        appendStyleSheet(v,'''
            .QLabel {
                font-size: 10px;
            }
        ''')
    
        h.addWidget(v)
        h.addStretch()
        h.addWidget(hbut)
        
        #b = QPushButton('quick')
        #bot.addWidget(b)
        #connect(b.clicked, lambda unused: self._quick())
        
        lay.addWidget(self.welcome)
        lay.addWidget(self.choose)
        lay.addLayout(bot)
        lay.addLayout(h)
        lay.setSpacing(0)
        lay.setContentsMargins(20,15,20,0)
        self.setLayout(lay)
    
    def _browse(self):
        d = QFileDialog()
        d.setFileMode(QFileDialog.Directory)
        d.setOption(QFileDialog.ShowDirsOnly)
        d.setViewMode(QFileDialog.Detail)
        #fixme: how to restrict this to just one folder??
        res = d.exec_()
        if not res:
            return
        
        folder = d.selectedFiles()[0]+'/'
        self.launch(folder)
        
    #def _quick(self):
    
    def launch(self,folder):
        if not os.path.exists(folder):
            jk.mkdir(folder)
        
        lock = LockFile(folder+'lock')
        if not lock.locked:
            self.choose.setText("ERROR:  Was unable to claim this project folder, check if another Design Explorer instance is currently using it.")
            return
        
        with StatusCatch(self.choose.setText) as err:
            self.main = Main(self._app_folder, folder, lock)
        
        if not err:
            self.accept()
        else:
            lock.unlock()

    def __call__(self,folder=None):
        if folder:
            self.setModal(True)
            self.show()
            self.launch(folder)
        self.exec_()

    def hclick(self):
    # fix-DM: on os.name=="posix", cannot return to Qt window after opening pdf
        if os.path.isdir(os.path.join(os.path.expanduser('~'),'.DesignExplorer/docs/manual')):
            self._doc_folder = os.path.join(os.path.expanduser('~'),'.DesignExplorer/docs/manual')
        else:
            self._doc_folder = os.getcwd()+'/docs/manual'
            
        filepath = self._doc_folder+'/explorer_manual.pdf'
        if sys.platform.startswith('darwin'):
            subprocess.call(('open', filepath))
        elif os.name == 'nt':
            os.startfile(filepath)
        elif os.name == 'posix':
            subprocess.call(('xdg-open', filepath))



@perr
def start(app_folder=None, project_folder=None,quick=False):
    # the preferred way to launch a project for DesignExplorer.  fairly new, will likely change.
    if app_folder is None:
        app_folder = os.path.join(os.path.expanduser('~'),'.DesignExplorer/')
    jk.mkdir(app_folder)
    
    dout("this window is just for debug info")
    dout("unless something goes wrong, you can ignore it!")
    dout("but if something does go wrong, please copy the text here and send it when asking for help")
    
    launcher = ProjectLauncher(app_folder)
    
    launcher(project_folder)
    return launcher.main
    
    
    
    