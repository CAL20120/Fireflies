import os 
import sys 
from datetime import datetime

from pxr import Usd, UsdGeom, Sdf

from PySide2 import QtCore
from PySide2 import QtWidgets
from PySide2 import QtGui


import hou
from fireflies.houdini import hou_utils


class importer_window(QtWidgets.QDialog):
    def __init__(self):
        super(importer_window, self).__init__()
        self.setWindowTitle("Import USD Asset")
        self.setMinimumSize(550, 700)

        self.create_widgets()
        self.create_layout()
        self.create_connections()

        self.get_asset_paths()
        # self.import_comment()

    def get_asset_paths(self):
        self.assets, self.paths = import_usd_asset.find_asset(self)
        
        self.assets_time = []
        for path in self.paths:
            time_map = os.path.getmtime(path)
            modified_time = datetime.fromtimestamp(time_map)
            self.assets_time.append(str(modified_time))
        
        self.refresh_asset_table()


    def create_widgets(self):
        self.asset_table = QtWidgets.QTableWidget()
        self.asset_table.setColumnCount(3)
        self.asset_table.setColumnWidth(0, 100)
        self.asset_table.setColumnWidth(1, 200)
        self.asset_table.setColumnWidth(2, 100)
        
        self.header = self.asset_table.horizontalHeader()
        self.asset_table.setHorizontalHeaderLabels(["Asset", "Local Path", "Date"])
        self.header.setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        
        
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

        self.comment_layout = QtWidgets.QHBoxLayout()

        self.bottom_btn_layout = QtWidgets.QHBoxLayout()
        self.bottom_btn_layout.addWidget(self.import_btn)
        self.bottom_btn_layout.addWidget(self.close_btn)
        # self.bottom_btn_layout.addWidget(self.debug_btn)
            
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.addLayout(self.table_layout)
        self.main_layout.addLayout(self.asset_info_layout)
        self.main_layout.addLayout(self.comment_layout)
        self.main_layout.addStretch()
        self.main_layout.addLayout(self.bottom_btn_layout)


    def create_connections(self):
        self.close_btn.clicked.connect(self.close)
        # self.debug_btn.clicked.connect(import_usd_asset.find_asset)
        # self.refresh_btn.clicked.connect(self.refresh_asset_table)
        self.import_btn.clicked.connect(self.import_asset)       

        self.asset_table.selectionModel().selectionChanged.connect(self.sel_changed)
        self.asset_table.selectionModel().selectionChanged.connect(self.import_comment)
        

    def refresh_asset_table(self):

        self.asset_table.setRowCount(0)

        for x in range(len(self.assets)):
            self.asset_table.insertRow(x)
            self.add_item(x, 0, self.assets[x])
            self.add_item(x, 1, self.paths[x])
            self.add_item(x, 2, self.assets_time[x])
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

        hou_utils.hou_usd.import_prod_usd_asset(self, asset_path=self.paths[target_index[1]])

    
    def import_comment(self):
        children = []
        for x in range(self.comment_layout.count()):
            child = self.comment_layout.itemAt(x).widget()
            if child:
                children.append(child)
        for child in children:
            child.deleteLater()
        
        self.text_edit_comment = QtWidgets.QTextEdit()
        self.text_edit_comment.setReadOnly(True)

        name, index  = self.sel_changed()
        asset_path = self.paths[index].rsplit("/", 1)[0]
        
        target_file = f"{asset_path}/metadata/commentary/{name}_comment.txt"

        with open(target_file, "r") as f:
            comment = f.read()
        self.text_edit_comment.setPlainText(comment)


        self.comment_layout.addWidget(self.text_edit_comment)


class import_usd_asset():
    def __init__(self):
        super(import_usd_asset, self).__init__()

    def find_asset(self):
        self.result_dirs = []
        self.result_published = []
        self.result_usd_path = []


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
