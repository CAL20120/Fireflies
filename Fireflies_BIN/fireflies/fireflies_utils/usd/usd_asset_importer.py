import os 
import sys 

from pxr import Usd, UsdGeom, Sdf

from PySide2 import QtCore
from PySide2 import QtWidgets
from PySide2 import QtGui

try:
    import maya.OpenMayaUI as omui
    from shiboken2 import wrapInstance
    import maya.cmds as cmds
    from fireflies.maya import maya_usd_import
except:
    import hou
    from fireflies.houdini import hou_utils

# import heapq

try:
    def maya_main_window():
        main_window_ptr = omui.MQtUtil.mainWindow()
        return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)
except:
    pass

class importer_window(QtWidgets.QDialog):
    def __init__(self):
        super(importer_window, self).__init__()
        self.setWindowTitle("Import USD Asset")
        self.setMinimumSize(450, 700)

        self.create_widgets()
        self.create_layout()
        self.create_connections()

        self.get_ft_paths()

    def get_ft_paths(self):
        self.assets, self.paths = import_usd_asset.find_asset(self)
        self.refresh_asset_table()


    def create_widgets(self):
        self.asset_table = QtWidgets.QTableWidget()
        self.asset_table.setColumnCount(4)
        self.asset_table.setColumnWidth(0, 150)
        self.asset_table.setColumnWidth(1, 70)
        self.asset_table.setColumnWidth(2, 100)
        self.asset_table.setColumnWidth(3, 70)
        self.header = self.asset_table.horizontalHeader()
        self.asset_table.setHorizontalHeaderLabels(["Asset", "Status", "Date", "Author"])


        # self.refresh_btn = QtWidgets.QPushButton("Refresh")
        # self.asset_info_table = QtWidgets.QTableWidget()
        # self.asset_info_table.setColumnCount(4)
        # self.vertical_header = self.asset_info_table.verticalHeader()
        # self.asset_info_table.setHorizontalHeaderLabels(["Asset", "test", "4", "8"])

        # self.debug_btn = QtWidgets.QPushButton("debug")
        self.import_btn = QtWidgets.QPushButton("Import")
        self.close_btn = QtWidgets.QPushButton("Close")

    def create_layout(self):
        self.table_layout = QtWidgets.QHBoxLayout()
        self.table_layout.addWidget(self.asset_table)
        # self.table_layout.addWidget(self.refresh_btn)

        self.asset_info_layout = QtWidgets.QHBoxLayout()
        # self.asset_info_layout.addWidget(self.asset_info_table)

        self.bottom_btn_layout = QtWidgets.QHBoxLayout()
        self.bottom_btn_layout.addWidget(self.import_btn)
        self.bottom_btn_layout.addWidget(self.close_btn)
        # self.bottom_btn_layout.addWidget(self.debug_btn)
            
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.addLayout(self.table_layout)
        self.main_layout.addLayout(self.asset_info_layout)
        self.main_layout.addStretch()
        self.main_layout.addLayout(self.bottom_btn_layout)


    def create_connections(self):
        self.close_btn.clicked.connect(self.close)
        # self.debug_btn.clicked.connect(import_usd_asset.find_asset)
        # self.refresh_btn.clicked.connect(self.refresh_asset_table)
        self.import_btn.clicked.connect(self.import_asset)       

        self.asset_table.selectionModel().selectionChanged.connect(self.sel_changed)

    #connections
    def refresh_asset_table(self):

        self.asset_table.setRowCount(0)

        for x in range(len(self.assets)):
            self.asset_table.insertRow(x)
            self.add_item(x, 0, self.assets[x])
            self.add_item(x, 1, self.paths[x])
            # self.add_item(x, 2, str(self.date_ft[x]))
            # self.add_item(x, 3, self.user_ft[x])

    def add_item(self, row, column, text) -> QtWidgets:
        item = QtWidgets.QTableWidgetItem(text)
        self.asset_table.setItem(row, column, item)


    def sel_changed(self):
        sel_item = self.asset_table.selectedItems()
        sel = sel_item[0]
        sel_name = sel.text()
        print(sel_name)
        item_index = sel_item[0].row()
        print(item_index)
        
        return sel_name, item_index


    def import_asset(self):
        print("importing usd asset: {}".format(self.sel_changed()[0]))
        # print(self.sel_changed()[1])
        target_index = self.sel_changed()
        print(self.paths[target_index[1]])

        try:
            maya_usd_import.maya_import_usd.import_usd(self, filepath=self.paths[target_index[1]])
        except:
            hou_utils.hou_usd.import_prod_usd_asset(self, asset_path=self.paths[target_index[1]])
            pass


class import_usd_asset():
    def __init__(self):
        super(import_usd_asset, self).__init__()

    def find_asset(self):
        self.result_dirs = []
        self.result_published = []
        self.result_usd_path = []

        try:
            self.prod_path = cmds.file(q=True, sn=True).rsplit("/", 4)[0].replace("/", "\\")
        except:
            self.prod_path = hou.hipFile.path().rsplit("/", 4)[0].replace("/", "\\")
        
        for dir, subdir, files in os.walk(self.prod_path):
            if "usd_published" in dir:
                self.result_dirs.append(dir)
        
        for index, dir in enumerate(self.result_dirs):
            for file in os.listdir(dir):
                if file.endswith(".usd"):
                    self.result_published.append(file.rsplit(".", 1)[0])
                    usd_path = os.path.join(dir, file).replace("\\", "/")
                    self.result_usd_path.append(usd_path)

        return self.result_published, self.result_usd_path



if __name__ == "__main__":
    x = importer_window()
    x.show()
