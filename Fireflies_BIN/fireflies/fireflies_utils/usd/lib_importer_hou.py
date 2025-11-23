import os 
import sys 
import time

from pxr import Usd, UsdGeom, Sdf

from PySide2 import QtCore
from PySide2 import QtWidgets
from PySide2 import QtGui

import hou 
from fireflies.houdini import hou_utils
from fireflies.fireflies_utils import fireflies_requests

class lib_importer_window(QtWidgets.QDialog):
    import_target = QtCore.Signal(str)

    def __init__(self, import_classic:bool=None, parent=hou.qt.mainWindow()):
        super(lib_importer_window, self).__init__(parent)
        self.nas_requests = fireflies_requests.nas_requests()
        
        self.import_classic = import_classic
        self.import_target = None

        self.prod_path = hou.hipFile.path().rsplit("/", 4)[0].replace("/", "\\")
        self.prod_path_curr = hou.hipFile.path().rsplit("/", 4)[0]
        
        self.setWindowTitle("Import Lib Asset")
        self.setMinimumSize(550, 700)

        self.create_widgets()
        self.create_layout()
        self.create_connections()

        self.get_elements()

    def create_widgets(self):
        self.filter_combo = QtWidgets.QComboBox()
        self.filter_combo.addItems(['Assets', 'Layouts','Lights'])

        self.asset_table = QtWidgets.QTableWidget()
        self.asset_table.setColumnCount(3)
        # self.asset_table.setColumnWidth(0, 100)
        # self.asset_table.setColumnWidth(1, 200)
        # self.asset_table.setColumnWidth(2, 100)
        self.header = self.asset_table.horizontalHeader()
        self.asset_table.setHorizontalHeaderLabels(["Asset", "Installed", "Path on server"])

        self.header.setSectionResizeMode(QtWidgets.QHeaderView.Stretch)

        self.import_btn = QtWidgets.QPushButton("Import")
        self.close_btn = QtWidgets.QPushButton("Close")


    def create_layout(self):
        self.table_layout = QtWidgets.QVBoxLayout()
        self.table_layout.addWidget(self.asset_table)

        self.bottom_btn_layout = QtWidgets.QHBoxLayout()
        self.bottom_btn_layout.addWidget(self.import_btn)
        self.bottom_btn_layout.addWidget(self.close_btn)
       
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.addWidget(self.filter_combo)
        self.main_layout.addLayout(self.table_layout, stretch=1)
        self.main_layout.addLayout(self.bottom_btn_layout)


    def create_connections(self):
        self.close_btn.clicked.connect(self.close)
        
        self.filter_combo.currentIndexChanged.connect(self.refresh_table)

        self.asset_table.selectionModel().selectionChanged.connect(self.sel_changed)

        self.import_btn.clicked.connect(self.import_asset)


    def add_item(self, row, column, text) -> QtWidgets:
        item = QtWidgets.QTableWidgetItem(text)
        self.asset_table.setItem(row, column, item)


    def current_selection(self):
        target_type = None
        
        if self.filter_combo.currentText() == "Asset":
            return self.assets, self.assets_path
        
        if self.filter_combo.currentText() == "Layouts":
            return self.layouts, self.assets_path
        
        if self.filter_combo.currentText() == "Lights":
            return self.lights, self.lights_path


    def refresh_table(self):
        try:
            selection, path = self.current_selection()
        except:
            selection = self.assets
            path = self.assets_path


        self.asset_table.setRowCount(0)

        for x in range(len(selection)):
            self.asset_table.insertRow(x)
            self.add_item(x, 0, selection[x])

            asset_name = path[x].rsplit("/", 1)[-1]
            print(asset_name)

            validate, asset_type, asset_path = self.nas_requests.check_local_instance(asset_name=asset_name, prod_path=self.prod_path_curr)

            if validate == True:
                self.add_item(x, 1, "Yes")
            else: 
                self.add_item(x, 1, "No")

            self.add_item(x, 2, path[x])


    def sel_changed(self):
        sel_item = self.asset_table.selectedItems()
        
        sel = sel_item[0]
        sel_name = sel.text()
        print(sel_name)
        
        item_index = sel_item[0].row()
        print(item_index)
        
        target_row = self.asset_table.rowCount() - 1
        target_test = self.asset_table.item(target_row, 0)

        return sel_name, item_index


    def get_elements(self):
        self.assets, self.layouts, self.lights, self.assets_path, self.lights_path = self.nas_requests.find_assets()
        self.refresh_table()


    def import_asset(self):
        _, item_index = self.sel_changed()

        nas_path = None

        if self.filter_combo.currentText() == 'Assets':
            nas_path = self.assets_path[item_index]
            print(nas_path)

        elif self.filter_combo.currentText() == 'Layouts':
            nas_path = self.assets_path[item_index]

        elif self.filter_combo.currentText() == 'Lights':
            nas_path = self.lights_path[item_index]

        asset_name = nas_path.rsplit("/", 1)[-1]

        if self.import_classic:
            self.nas_requests.download_asset(nas_path=nas_path, asset_name=asset_name, prod_path=self.prod_path_curr)

        else: 
            hip_path = self.nas_requests.download_asset(nas_path=nas_path, asset_name=asset_name, prod_path=self.prod_path_curr, disable_import=True)

            self.import_target.parm('input_light2').set(hip_path)

        self.refresh_table()


if __name__ == "__main__":
    x = lib_importer_window()
    x.show()
