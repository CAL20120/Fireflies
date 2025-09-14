import os
import maya.cmds as cmds 
import maya.mel as mel 

import tempfile

import mayaUsd
from mayaUsdLibRegisterStrings import getMayaUsdLibString

from pxr import Usd, Sdf

from PySide2 import QtCore
from PySide2 import QtWidgets
from PySide2 import QtGui
import maya.OpenMayaUI as omui
from shiboken2 import wrapInstance

class maya_to_usd():
    def __init__(self):
        super(maya_to_usd, self).__init__()
        self.export_path = r"D:\chris\asset_checker\test_scenes\usd_test_sample.usda"
        self.export_dir = r"D:\chris\asset_checker\test_scenes\temp"
        self.export_temp = r"D:\chris\usd_import_export_maya\tests_exports_temp"


    def check_exists(self, path):
        if os.path.exists(self.export_path):
            return True
        else: 
            return False


    def export_usd(self, output_dir) -> mayaUsd:

        # if self.check_exists() == True:
        #     return

        initial_sel = (cmds.ls(sl = True))
        if not initial_sel:
            print("No active selection")
            return

        family_sel = cmds.listRelatives(initial_sel, fullPath=True)

        sel_name = cmds.ls(sl = True)[0]

        cmds.select(family_sel)
        print(family_sel)

        print(initial_sel[0])
        self.project_path_ex = r"D:\chris\usd_import_export_maya\tests_exports_temp"
        self.export_full = f"{self.project_path_ex}\\{initial_sel[0]}.usd"
        print(self.export_full)


        temp = tempfile.NamedTemporaryFile(prefix = "USD", suffix = ".usd", dir = output_dir)
        print(f"\n {temp.name} \n")
        print(temp)


        #when temp is called, it writes the file, yet the file stays open while we don't tell temp to close it 
        #if we don't do so, maya can't edit it and add the usd data to it
        temp.close()
        cmds.mayaUSDExport(
            file = temp.name,
            selection = True,
            shadingMode = "useRegistry"
        )
        

        transform = cmds.createNode("transform", name = f"{family_sel[0]}")
        proxyShapeTest = cmds.createNode('mayaUsdProxyShape', name = "%s_ProxyShape" % family_sel[0], parent = transform)

        #we need to attribute the layer to the new proxyShape
        cmds.setAttr(f"{proxyShapeTest}.filePath", temp.name, type = "string")


        # A ne surtout pas faire, sinon on supprime effectivement le proxy, mais les données usd restent en mémoire dans maya
        # et deviennent inaccessibles.
        "cmds.delete(proxyShapeTest)"

        # os.close(self.export_full)
        # os.remove(self.export_full)

        temp.close()
        temp.delete(True)

        print("\n Usd file exported to %s! \n" % temp.name)


def maya_main_window(): 
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)

class usd_export_window(QtWidgets.QDialog):
    def __init__(self, parent = maya_main_window()):
        super(usd_export_window, self).__init__(parent)

        # self.file_filters = "USD binary (*.usdc *.usd *.usdz);; USD ASCII (*.usda);; All Files (*.*)"
        # self.selected_filter = "USD binary (*.usdc *.usd *.usdz)"

        self.setWindowTitle("USD Export")
        self.setMinimumSize(350, 50)

        self.create_widgets()
        self.create_layout()
        self.create_connections()

    def create_widgets(self):
        self.dir_path_edit = QtWidgets.QLineEdit()

        self.open_sel_file = QtWidgets.QPushButton()
        self.open_sel_file.setIcon(QtGui.QIcon(":fileSave.png"))
        self.open_sel_file.setToolTip("Select output for USD file")
        # pass

        ## Buttons to select the type of import (either, simple import stage / as a sublayer / 
        # or collapse the current active layer)
        self.export_path = QtWidgets.QRadioButton("Export to disk")
        self.export_path.setChecked(True)
        self.export_path.setToolTip("Export permanent USD file")

        self.export_temp = QtWidgets.QRadioButton("Temorary")
        self.export_temp.setToolTip("Output USD file as a temporary file")

        self.export_button = QtWidgets.QPushButton("Export")
        self.export_button.setToolTip("Export USD file")
        self.close_button = QtWidgets.QPushButton("Close")

        self.usda_button = QtWidgets.QCheckBox("usda")
        self.usd_button = QtWidgets.QCheckBox("usd")


    def create_layout(self):
        file_layout = QtWidgets.QHBoxLayout()
        file_layout.addWidget(self.dir_path_edit)
        file_layout.addWidget(self.open_sel_file)

        form_layout = QtWidgets.QFormLayout()
        form_layout.addRow("Output: ", file_layout)

        export_opts_layout = QtWidgets.QHBoxLayout()
        export_opts_layout.addWidget(self.export_path)
        export_opts_layout.addWidget(self.export_temp)
        form_layout.addRow("", export_opts_layout)

        form_layout_opts = QtWidgets.QFormLayout()
        format_opts_layout = QtWidgets.QHBoxLayout()
        format_opts_layout.addWidget(self.usd_button)
        format_opts_layout.addWidget(self.usda_button)
        # form_layout.addRow("Export Format :", form_layout_opts)
        form_layout_opts.addRow("export format :", format_opts_layout)

        bottom_button_layout = QtWidgets.QHBoxLayout()
        bottom_button_layout.addStretch()
        bottom_button_layout.addWidget(self.export_button)
        bottom_button_layout.addWidget(self.close_button)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addLayout(form_layout)
        main_layout.addLayout(form_layout_opts)
        main_layout.addLayout(bottom_button_layout)
        


    def create_connections(self):
        self.open_sel_file.clicked.connect(self.print_test)

        self.export_path.toggled.connect(self.export_to_path_usd)
        self.export_temp.toggled.connect(self.export_temp_usd)

        self.open_sel_file.clicked.connect(self.open_sel_dialog)

        self.export_button.clicked.connect(self.export_apply)
        self.close_button.clicked.connect(self.close)
        pass


    # Connections methods 

    def export_to_path_usd(self):
        pass

    def export_temp_usd(self):
        pass


    def open_sel_dialog(self):
        dir = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select Output", "")

        if dir:
            self.dir_path_edit.setText(dir)
            print(dir)

        else:
            print("No directory selected")

        return dir
    
    def export_apply(self):
        maya_to_usd.export_usd(self, self.dir_path_edit.text())
        pass


    def print_test(self):
        print("working")


if __name__ == "__main__":
    x = usd_export_window()
    x.show()
