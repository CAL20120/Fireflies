import os
import maya.cmds as cmds 
import maya.mel as mel 

from pxr import Usd, Sdf, UsdGeom

from PySide2 import QtWidgets, QtCore, QtGui

import maya.OpenMayaUI as omui
from shiboken2 import wrapInstance


def maya_main_window():
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)


class create_usd_asset_window(QtWidgets.QDialog):
    def __init__(self, parent = maya_main_window()):
        super(create_usd_asset_window, self).__init__(parent)
        self.setWindowTitle("Create a Production Asset")
        self.setMinimumSize(350, 100)

        self.create_widgets()
        self.create_layout()
        self.create_connections()

        if self.sel():
            self.active_sel = self.sel()[0]

        self.asset_name = f"{self.input_name.text()}_ASSET"



    def sel(self) -> list:
        initial_sel = cmds.ls(sl=True)
        if not initial_sel:
            print("no active selection")
            return
        family_sel = cmds.listRelatives(initial_sel, fullPath = True)
        return initial_sel, True



    def create_widgets(self):
        self.input_name = QtWidgets.QLineEdit()

        self.check_import_active = QtWidgets.QCheckBox("Import active selection")

        ##bottom buttons
        self.close_btn = QtWidgets.QPushButton("Close")
        self.create_btn = QtWidgets.QPushButton("Create asset")

        self.check_btn = QtWidgets.QPushButton("Check asset")
        self.debug_btn = QtWidgets.QPushButton("Debug")



    def create_layout(self):
        self.line_layout = QtWidgets.QFormLayout()
        self.line_layout.addRow("Asset name :", self.input_name)
        self.line_layout.addRow("", self.check_import_active)
        # self.line_layout.addRow("", self.check_btn)
        # self.line_layout.addWidget(self.debug_btn)
        # self.line_layout.addRow("", self.debug_btn)

        self.button_layout = QtWidgets.QHBoxLayout()
        self.button_layout.addStretch()
        self.button_layout.addWidget(self.create_btn)
        self.button_layout.addWidget(self.close_btn)

        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.addLayout(self.line_layout)
        self.main_layout.addLayout(self.button_layout)


    def create_connections(self):
        self.input_name.textChanged.connect(self.udpate_name)

        self.close_btn.clicked.connect(self.close)
        self.create_btn.clicked.connect(self.create_usd_hierarchy)
        self.check_import_active.stateChanged.connect(self.update_sel)

        # self.debug_btn.clicked.connect(self.debug)
        # self.check_btn.clicked.connect(self.check)


    def update_sel(self):
        self.active_sel = self.sel()[0]
        print(f"active selection : {self.active_sel}")
        return self.active_sel
    


    def udpate_name(self):
        self.asset_name = f"{self.input_name.text()}_ASSET"
        return self.asset_name
    


    def create_usd_hierarchy(self):
        self.transform = cmds.createNode("transform", name = f"{self.input_name.text()}_ASSET")
        geo_xform = cmds.createNode("transform", name = "GEO")
        

        self.geo_xform_proxy = cmds.createNode("transform", name = "proxy")
        self.geo_xform_render = cmds.createNode("transform", name = "render")


        mtl_xform = cmds.createNode("transform", name = "mtl")

        cmds.parent(geo_xform, mtl_xform, self.transform)
        cmds.parent(self.geo_xform_proxy, self.geo_xform_render, geo_xform)


        if self.check_import_active.isChecked() == True:
            cmds.parent(self.active_sel, self.geo_xform_render)


        print("### ASSET CREATED ###")



if __name__ == "__main__":
    x = create_usd_asset_window()
    x.show()

