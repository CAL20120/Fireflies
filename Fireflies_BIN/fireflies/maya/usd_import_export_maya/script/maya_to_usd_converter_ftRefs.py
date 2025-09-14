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

from cgev.pipeline.data import session
from cgev.common import environment
import ftrack_api

class maya_to_usd():
    def __init__(self):
        super(maya_to_usd, self).__init__()
        self.export_path = r"D:\chris\asset_checker\test_scenes\usd_test_sample.usda"
        self.export_dir = r"D:\chris\asset_checker\test_scenes\temp"
        self.export_temp = r"D:\chris\usd_import_export_maya\tests_exports_temp"

        self.context = session.getContext()

        self.project = self.context.getProjectName()
        self.sequence = self.context.getSequenceName()
        self.shot = self.context.getShotName()

        self.task = self.context.getTaskName()
        self.task_id = self.context.getTaskId()

        self.sessionFT = session.getSessionFT()
        self.manager = session.getManager()

        self.find_sel()
        self.build_path_ft()
        self.export_usd()

    def find_sel(self):
        initial_sel = (cmds.ls(sl = True))
        if not initial_sel:
            print("No active selection")
            return  False
        family_sel = cmds.listRelatives(initial_sel, fullPath=True)

        return initial_sel[0], family_sel, True

    def build_path_ft(self):
        if self.find_sel()[2] == False:
            return

        print(self.project)
        print(self.task_id)
        print(self.sessionFT)
        print(self.manager.getShot(self.project, self.sequence, self.shot))

        asset_name = self.find_sel()[0]
        print(asset_name)

        test_query = f"select name from Task where id is {self.task_id}"
        task_ft = self.sessionFT.query(test_query).first()
        print(task_ft)


        ##checking is asset exists 
        query_asset = f"Asset where name is {asset_name} and parent.id is {self.context.getShotId()}"
        asset_ft = self.sessionFT.query(query_asset).first()


        if asset_ft == None:
            query_type = 'AssetType where name is "{}"'.format("Usd Layer")
            asset_type = self.sessionFT.query(query_type).first()

            query_sh_id = f"Shot where id is {self.context.getShotId()}"
            shot_ft = self.sessionFT.query(query_sh_id).first()

            asset_ft = self.sessionFT.create(
                "Asset",
                {
                    "name": asset_name,
                    "type": asset_type, 
                    "parent": shot_ft,
                },
            )
            
        
        user = environment.getUser()
        query_user = f"User where username is {user}"
        user_ft = self.sessionFT.query(query_user).first()

        version_ft = self.sessionFT.create(
            "AssetVersion",
            {
                "asset": asset_ft,
                "task": task_ft,
                "user": user_ft,
                "comment": f"test usd publish : {asset_name}",
            },
        )

        query = 'Location where name is "ftrack.unmanaged"'
        location = self.sessionFT.query(query).first()
        
        #for maya
        self.scene_path = cmds.file(q=True, sn=True).rsplit("/", 2)[0]
        self.asset_path = f"{self.scene_path}/usd/{self.find_sel()[0]}.usd"
        print(self.asset_path)

        component = version_ft.create_component(path=self.asset_path, data={"name":"main"}, location=location)

        version_ft["custom_attributes"]["linkedto"] = os.path.basename(self.asset_path)

        try: 
            print("commit")
            self.sessionFT.commit()
        except:
            print("rollback")
            self.sessionFT.rollback()

        self.export_usd()

        return self.asset_path

    def export_usd(self) -> mayaUsd:

        cmds.select(self.find_sel()[1])

        # self.project_path_ex = r"D:\chris\usd_import_export_maya\tests_exports_temp"
        # self.export_full = f"{self.project_path_ex}\\{self.find_sel()[0]}.usd"
        # print(self.export_full)

        temp = tempfile.NamedTemporaryFile(prefix = "USD", suffix = ".usd")
        # print(f"\n {temp.name} \n")
        # print(temp)


        #when temp is called, it writes the file, yet the file stays open while we don't tell temp to close it 
        #if we don't do so, maya can't edit it and add the usd data to it
        temp.close()

        cmds.mayaUSDExport(
            file = self.asset_path,
            selection = True,
            shadingMode = "useRegistry"
        )

        transform = cmds.createNode("transform", name = f"{self.find_sel()[1]}")
        proxyShapeTest = cmds.createNode('mayaUsdProxyShape', name = "%s_ProxyShape" % self.find_sel()[1], parent = transform)

        #we need to attribute the layer to the new proxyShape
        cmds.setAttr(f"{proxyShapeTest}.filePath", self.asset_path, type = "string")


        # A ne surtout pas faire, sinon on supprime effectivement le proxy, mais les données usd restent en mémoire dans maya
        # et deviennent inaccessibles.
        "cmds.delete(proxyShapeTest)"

        # os.close(self.export_full)
        # os.remove(self.export_full)

        temp.close()
        temp.delete(True)

        print("\n Usd file exported to %s! \n" % self.asset_path)


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

    # x = maya_to_usd()
    # x.export_usd()