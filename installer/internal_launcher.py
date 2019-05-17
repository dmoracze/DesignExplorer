# second stage launching script for DesignExplorer
from DesignExplorer import *
import sys

mw = start()

mw.window.resize(QSize(752, 472))

mw.splitter.setSizes([105, 71, 264])
mw.window.resize(QSize(1100,900))

app = QApplication.instance()
sys.exit(app.exec_())