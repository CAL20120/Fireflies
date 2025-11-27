from PySide2 import QtWidgets

import os

import hou
from fireflies.houdini import hou_utils


class hip_importer(QtWidgets.QDialog):
    def __init__(self, parent=hou.qt.mainWindow()):
        super(hip_importer, self).__init__(parent)

        self.utils = hou_utils.hou_usd()
        
        self.file_filters = "USD binary (*.usdc *.usd *.usdz);; USD ASCII (*.usda);; All Files (*.*)"
        self.selected_filter = "All Files (*.*)"

        self.setWindowTitle("HIP importer")
        self.setMinimumSize(250, 100)

        self.create_widgets()
        self.create_layout()
        self.create_connections()


    def create_widgets(self):     
        self.input_path = QtWidgets.QLineEdit()
        self.open_sel = QtWidgets.QPushButton()
        self.open_sel.setIcon(hou.ui.createQtIcon("BUTTONS_chooser_folder"))
        
        self.convert_btn = QtWidgets.QPushButton("Convert Path")
        self.import_btn = QtWidgets.QPushButton("Import")
        self.close_btn = QtWidgets.QPushButton("Close")


    def create_layout(self):
        self.top_layout = QtWidgets.QHBoxLayout()
        self.top_layout.addWidget(self.input_path)
        self.top_layout.addWidget(self.open_sel)

        self.button_layout = QtWidgets.QHBoxLayout()
        self.button_layout.addWidget(self.convert_btn)
        self.button_layout.addWidget(self.import_btn)
        self.button_layout.addWidget(self.close_btn)

        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.addLayout(self.top_layout)
        self.main_layout.addLayout(self.button_layout)


    def create_connections(self):
        self.open_sel.clicked.connect(self.open_file_dialog)
        self.close_btn.clicked.connect(self.close)

        self.import_btn.clicked.connect(self.import_asset)
        self.convert_btn.clicked.connect(self.convert_path)


    def convert_path(self):
        input_path = self.input_path.text()
        
        if not input_path:
            print('no current path')
            return
        
        print("input path: %s" %input_path)

        hip_path = self.utils.path_converter(path=input_path)

        self.input_path.clear()
        self.input_path.setText(hip_path)


    def open_file_dialog(self):
        file_path, self.selected_filter = QtWidgets.QFileDialog.getOpenFileName(
            self, "Select USD file", "", self.file_filters, self.selected_filter
        ) 
        
        if file_path:
            self.input_path.setText(file_path)
            print(file_path)
            print("file name : %s" % file_path.rsplit("/", 1)[1])
            
        else:
            print("No file selected")


    def import_asset(self):
        print('importing asset')

        asset_path = self.input_path.text()
        if not asset_path:
            print("no current path in input")
            return

        asset_path = self.utils.path_converter(path=asset_path)

        if any(ext in asset_path for ext in ['.usd', '.usda', '.usdz']):
            self.utils.import_prod_usd_asset(asset_path=asset_path)

        else: 
            self.utils.import_regular_asset(asset_path=asset_path)



if __name__ == "__main__":
    x = hip_importer()
    x.show()