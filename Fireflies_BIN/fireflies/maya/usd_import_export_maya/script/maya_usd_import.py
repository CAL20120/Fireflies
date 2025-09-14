from PySide2 import QtCore
from PySide2 import QtWidgets
from PySide2 import QtGui

import os 

import maya.cmds as cmds 
import maya.OpenMayaUI as omui
from shiboken2 import wrapInstance

from pxr import Usd, UsdGeom, Sdf

class maya_import_usd():
    def __init__(self):
        super(maya_import_usd, self).__init__()

    def import_usd(self, filepath):
        stage = Usd.Stage.Open(filepath)
        print(stage)

        # IF we import the usd file with the official cmds command, it will import the usd data as standard data
        # not into a proxy shape (that reads correctly usd data), and possibly, if we import the usd data 
        # through the official command, it will only import certain prims, and they'll be empty... 

        cmds.mayaUSDImport(
            file = filepath,
            primPath = "/",
            importInstances = True,
            excludePrimvar = "None"
            # shadingMode = "useRegistry"
        )
        file_name = filepath.rsplit("/", 1)[1]
        transform = cmds.createNode("transform", name = file_name.split(".", 1)[0])
        proxyShape = cmds.createNode("mayaUsdProxyShape", name = "%s_proxy" %file_name, parent = transform)

        cmds.setAttr(f"{proxyShape}.filePath", filepath, type = "string")
        return


def maya_main_window(): 
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)

class usd_import_window(QtWidgets.QDialog):
    def __init__(self, parent = maya_main_window()):
        super(usd_import_window, self).__init__(parent)

        self.file_filters = "USD binary (*.usdc *.usd *.usdz);; USD ASCII (*.usda);; All Files (*.*)"
        self.selected_filter = "USD binary (*.usdc *.usd *.usdz)"

        self.setWindowTitle("Usd Import")
        self.setMinimumSize(350, 50)

        self.create_widgets()
        self.create_layout()
        self.create_connections()

    def create_widgets(self):
        self.file_path_edit = QtWidgets.QLineEdit()

        self.open_sel_file = QtWidgets.QPushButton()
        self.open_sel_file.setIcon(QtGui.QIcon(":fileOpen.png"))
        self.open_sel_file.setToolTip("Select USD file")
        # pass

        ## Buttons to select the type of import (either, simple import stage / as a sublayer / 
        # or collapse the current active layer)
        self.open_stage = QtWidgets.QRadioButton("Open stage")
        self.open_stage.setChecked(True)
        self.add_sublayer = QtWidgets.QRadioButton("Add sublayer")

        self.import_button = QtWidgets.QPushButton("Import")
        self.import_button.setToolTip("Import selected USD file")
        self.close_button = QtWidgets.QPushButton("Close") 


    def create_layout(self):
        file_layout = QtWidgets.QHBoxLayout()
        file_layout.addWidget(self.file_path_edit)
        file_layout.addWidget(self.open_sel_file)

        form_layout = QtWidgets.QFormLayout()
        form_layout.addRow("File: ", file_layout)

        import_opts_layout = QtWidgets.QHBoxLayout()
        import_opts_layout.addWidget(self.open_stage)
        import_opts_layout.addWidget(self.add_sublayer)
        form_layout.addRow("", import_opts_layout)

        bottom_button_layout = QtWidgets.QHBoxLayout()
        bottom_button_layout.addStretch()
        bottom_button_layout.addWidget(self.import_button)
        bottom_button_layout.addWidget(self.close_button)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addLayout(form_layout)
        main_layout.addLayout(bottom_button_layout)


    def create_connections(self):
        self.open_sel_file.clicked.connect(self.print_test)

        self.open_stage.toggled.connect(self.update_force_visibility)
        self.open_sel_file.clicked.connect(self.open_sel_dialog)

        self.import_button.clicked.connect(self.import_apply_load) 
        self.close_button.clicked.connect(self.close)
        pass


    # Connections methods 

    def update_force_visibility(self, checked):
        pass

    def open_sel_dialog(self):
        file_path, self.selected_filter = QtWidgets.QFileDialog.getOpenFileName(
            self, "Select USD file", "", self.file_filters, self.selected_filter
        )
        
        if file_path:
            self.file_path_edit.setText(file_path)
            print(file_path)
            print("file name : %s" % file_path.rsplit("/", 1)[1])
            
        else:
            print("No file selected")

        return file_path


    def import_apply_load(self):
        maya_import_usd.import_usd(self, self.file_path_edit.text())
        print(self.file_path_edit.text())
        self.close()

    def print_test(self):
        print("working")



test = usd_import_window()

test.show()
