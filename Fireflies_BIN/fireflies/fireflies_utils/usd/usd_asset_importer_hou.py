import os 
import sys 
from datetime import datetime
import subprocess
import re

import collections

from pxr import Usd, UsdGeom, Sdf

from PySide2 import QtCore
from PySide2 import QtWidgets
from PySide2 import QtGui


import hou
from fireflies.houdini import hou_utils
# from fireflies.fireflies_utils.usd import fireflies_usd_viewer


class importer_window(QtWidgets.QDialog):
    def __init__(self):
        super(importer_window, self).__init__()
        self.setWindowTitle("Import USD Asset")
        self.setMinimumSize(600, 700)

        self.create_widgets()
        self.create_layout()
        self.create_connections()

        self.get_asset_paths()
        # self.import_comment()

    def get_asset_paths(self):
        self.prod_path = hou.hipFile.path().rsplit("/", 4)[0].replace("/", "\\")

        test = import_usd_asset()
        self.assets_name, self.assets_vars = test.find_asset()

        # self.assets_time = []
        # for path in self.paths:
        #     time_map = os.path.getmtime(path)
        #     modified_time = datetime.fromtimestamp(time_map)
        #     self.assets_time.append(str(modified_time))
        

        self.refresh_asset_table()


    def create_widgets(self):
        self.asset_table = QtWidgets.QTableWidget()
        self.asset_table.setColumnCount(4)
        
        self.header = self.asset_table.horizontalHeader()
        self.asset_table.setHorizontalHeaderLabels(["Asset", "Version", "Local Path", "Date"])
        self.header.setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        
        self.preview_btn = QtWidgets.QPushButton("Preview Asset")
        
        # self.refresh_btn = QtWidgets.QPushButton("Refresh")
        # self.asset_info_table = QtWidgets.QTableWidget()
        # self.asset_info_table.setColumnCount(4)
        # self.vertical_header = self.asset_info_table.verticalHeader()
        # self.asset_info_table.setHorizontalHeaderLabels(["Asset", "test", "4", "8"])

        # self.debug_btn = QtWidgets.QPushButton("debug")
        self.import_btn = QtWidgets.QPushButton("Import")
        self.close_btn = QtWidgets.QPushButton("Close")


    def create_layout(self):
        self.table_layout = QtWidgets.QVBoxLayout()
        self.table_layout.addWidget(self.asset_table)
        self.table_layout.addWidget(self.preview_btn)
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
        # self.asset_table.selectionModel().selectionChanged.connect(self.import_comment)

        self.preview_btn.clicked.connect(self.show_preview)
        

    def refresh_asset_table(self):

        self.asset_table.setRowCount(0)

        for x, asset in enumerate(self.assets_name):
            asset_versions = list(self.assets_vars[asset].keys())

            self.asset_table.insertRow(x)
            self.add_item(x, 0, asset)

            self.version_combo = QtWidgets.QComboBox()
            self.version_combo.addItems(asset_versions)
            self.version_combo.setProperty('row', x)

            self.version_combo.currentTextChanged.connect(self.refresh_version)
            self.asset_table.setCellWidget(x, 1, self.version_combo)

            target_version = asset_versions[0]
            asset_path = self.assets_vars[asset][target_version]
            self.add_item(x, 2, asset_path)

            time_map = os.path.getmtime(asset_path)
            modified_time = datetime.fromtimestamp(time_map)
            self.add_item(x, 3, modified_time)


        # for x in range(len(self.assets)):
        #     self.combo_test = QtWidgets.QComboBox()
        #     self.asset_table.insertRow(x)
        #     self.add_item(x, 0, self.assets[x])

        #     self.combo_test.addItem(self.assets[x])
        #     self.asset_table.setCellWidget(x, 1, self.combo_test)

        #     self.add_item(x, 2, self.paths[x])
        #     self.add_item(x, 3, self.assets_time[x])
        #     # self.add_item(x, 2, str(self.date_ft[x]))
        #     # self.add_item(x, 3, self.user_ft[x])


    def refresh_version(self):

        #we need the get the qt signel to know which version changed in the ui
        target_combo = self.sender()
        target_row = target_combo.property('row')

        asset = self.asset_table.item(target_row, 0).text()

        asset_versions = sorted(self.assets_vars[asset].keys())

        index = target_combo.currentIndex()

        target_version = asset_versions[index]

        path = self.assets_vars[asset][target_version]

        self.asset_table.item(target_row, 2).setText(path)

        time_map = os.path.getmtime(path)
        modified_time = datetime.fromtimestamp(time_map)
        self.asset_table.setItem(target_row, 3, QtWidgets.QTableWidgetItem(str(modified_time)))




    def add_item(self, row, column, text) -> QtWidgets:
        item = QtWidgets.QTableWidgetItem(str(text))
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
        sel_name, target_index = self.sel_changed()

        target_combo = self.asset_table.cellWidget(target_index, 1)
        target_version = target_combo.currentIndex()

        asset = self.asset_table.item(target_index, 0).text()

        asset_versions = sorted(self.assets_vars[asset].keys())
        version = asset_versions[target_version]

        path = self.assets_vars[asset][version]

        hou_utils.hou_usd.import_prod_usd_asset(self, asset_path=path)

    
    # def import_comment(self):
    #     children = []
    #     for x in range(self.comment_layout.count()):
    #         child = self.comment_layout.itemAt(x).widget()
    #         if child:
    #             children.append(child)
    #     for child in children:
    #         child.deleteLater()
        
    #     self.text_edit_comment = QtWidgets.QTextEdit()
    #     self.text_edit_comment.setReadOnly(True)

    #     name, index  = self.sel_changed()
    #     asset_path = self.paths[index].rsplit("/", 1)[0]
        
    #     target_file = f"{asset_path}/metadata/commentary/{name}_comment.txt"

    #     with open(target_file, "r") as f:
    #         comment = f.read()
    #     self.text_edit_comment.setPlainText(comment)

    #     self.comment_layout.addWidget(self.text_edit_comment)

    # def show_preview(self):
    #     _, index = self.sel_changed()
    #     self.x = hou_utils.hou_usd()
        
    #     target_path = self.paths[index]
    #     print(target_path)
    #     self.x.show_preview(asset_path=target_path)



    def show_preview(self):
        name, index  = self.sel_changed()
        asset_path = self.paths[index]

        asset_path = asset_path.replace("/", "\\")
        print("opening ###### {}".format(asset_path))

        # asset_path = "R:\\Christopher_LUCAS\\PRODS\\test_dev\\001\\01\\model\\usd_published\\test_ASSET.usd"
        # fireflies_usd_viewer(asset_path=asset_path)


class import_usd_asset():
    def __init__(self):
        super(import_usd_asset, self).__init__()


    def find_asset(self):
        #the purpose here is to build a dict with each assets and its version to 
        #make the asset versions tracking easier 
        self.assets_vars = collections.defaultdict(dict)


        # self.result_dirs = []
        # self.result_published = []
        # self.result_usd_path = []

        self.prod_path = hou.hipFile.path().rsplit("/", 4)[0].replace("/", "\\")
        

        self.usd_publied_dir = []
        for root, subdir, files in os.walk(self.prod_path):
            if "usd_published" in subdir:
                self.usd_publied_dir.append(os.path.join(root, "usd_published"))

        self.assets = []
        for dirs in self.usd_publied_dir:
            for asset in os.listdir(dirs):
                asset_dir = os.path.join(dirs, asset)

                if os.path.isdir(asset_dir):
                    self.assets.append(asset_dir)


        self.asset_versions = []
        for asset_dir in self.assets:
            for version in os.listdir(asset_dir):
                version_dir = os.path.join(asset_dir, version)

                if os.path.isdir(version_dir):
                    self.asset_versions.append(version_dir)


        self.asset_file = []
        for version_dir in self.asset_versions:
            for file in os.listdir(version_dir):
                if file.endswith(".usd"):
                    asset_path = os.path.join(version_dir, file)
                    correct_path = asset_path.replace("\\", "/")
                    self.asset_file.append(correct_path)

        #time to build the dict

        target_pattern = re.compile(r'(.*)\.usd$')
        for asset in self.asset_file:
            file = os.path.basename(asset)

            target = target_pattern.match(file)
            if not target:
                continue

            name = target.group(1)

            version_fld = os.path.basename(os.path.dirname(asset))

            target_version = re.search(r'(\d+)$', version_fld)
            if not target_version:
                continue

            version = target_version.group(1)
            version_path = f"{int(version):03d}"

            self.assets_vars[name][version_path] = asset


        # for dir, subdir, files in os.walk(self.prod_path):
        #     if "usd_published" in dir:
        #         self.result_dirs.append(dir)        

        # for index, dir in enumerate(self.result_dirs):
        #     for file in os.listdir(dir):
                
        #         if file.endswith(".usd"):
        #             self.result_published.append(file.rsplit(".", 1)[0])
        #             usd_path = os.path.join(dir, file).replace("\\", "/")
        #             self.result_usd_path.append(usd_path)

        # return self.result_published, self.result_usd_path

        print(self.assets_vars)

        return list(self.assets_vars.keys()), self.assets_vars


x = importer_window()
x.show()

