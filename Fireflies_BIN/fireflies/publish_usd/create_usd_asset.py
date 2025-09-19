import os
import maya.cmds as cmds 
import maya.mel as mel 

from pxr import Usd, Sdf, UsdGeom

from PySide2 import QtCore
from PySide2 import QtWidgets
from PySide2 import QtGui
import maya.OpenMayaUI as omui
from shiboken2 import wrapInstance

# import tempfile


def maya_main_window():
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)


class create_usd_asset_window(QtWidgets.QDialog):
    def __init__(self, parent = maya_main_window()):
        super(create_usd_asset_window, self).__init__(parent)
        self.setWindowTitle("Create USD Asset")
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

        self.import_active_chk = QtWidgets.QCheckBox("Import active selection")

        ##bottom buttons
        self.close_btn = QtWidgets.QPushButton("Close")
        self.create_btn = QtWidgets.QPushButton("Create asset")

        self.check_btn = QtWidgets.QPushButton("Check asset")
        self.debug_btn = QtWidgets.QPushButton("Debug")

    def create_layout(self):
        self.line_layout = QtWidgets.QFormLayout()
        self.line_layout.addRow("Asset name :", self.input_name)
        self.line_layout.addRow("", self.import_active_chk)
        self.line_layout.addRow("", self.check_btn)
        self.line_layout.addWidget(self.debug_btn)
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
        self.import_active_chk.stateChanged.connect(self.update_sel)

        self.debug_btn.clicked.connect(self.debug)
        self.check_btn.clicked.connect(self.check)


    def update_sel(self):
        self.active_sel = self.sel()[0]
        print(f"active selection : {self.active_sel}")
        return self.active_sel
    
    def udpate_name(self):
        self.asset_name = f"{self.input_name.text()}_ASSET"
        return self.asset_name
    

    def create_usd_hierarchy(self):

        self.transform = cmds.createNode("transform", name = f"{self.input_name.text()}_ASSET")
        geo_xform = cmds.createNode("transform", name = "geo")
        self.geo_xform_proxy = cmds.createNode("transform", name = "proxy")
        self.geo_xform_render = cmds.createNode("transform", name = "render")

        mtl_xform = cmds.createNode("transform", name = "mtl")

        cmds.parent(geo_xform, mtl_xform, self.transform)
        cmds.parent(self.geo_xform_proxy, self.geo_xform_render, geo_xform)

        if self.import_active_chk.isChecked() == True:
            cmds.parent(self.active_sel, self.geo_xform_render)
            print("//Geo parented to hierarchy !")


        cube = cmds.polyCube(name="Asset")
        cmds.parent(cube, self.geo_xform_render)
        print("usd hierarchy created")

    # def add_sel_hierarchy(self):
    #     cmds.parent(self.active_sel, self.geo_xform_render)
    #     pass

    def debug(self):
        print(self.asset_name)
        pass

    def check(self):
        self.shot_path = cmds.file(q=True, sn=True).rsplit("/", 2)[0]
        export_path = "%s/test_02/test.usda" % self.shot_path
        self.final_sel = cmds.listRelatives(self.asset_name, fullPath=True)
        usd_check_hierarchy.export_usd_tmp_check(self, selection=self.final_sel, export_path=export_path)

    def test(self):
        print(f"{self.input_name.text()}_asset")


class usd_check_hierarchy():
    def __init__(self):
        super(usd_check_hierarchy, self).__init__()
        
        # self.export_path = f"{self.shot_path}/tmp/{create_usd_asset_window().asset_name}.usd"
        # for prim in stage.Traverse():
        #     if prim.GetPrimAtPath(f"{create_usd_asset_window.}"):
        #         print(prim)

    def export_usd_tmp_check(self, selection, export_path) -> Usd: 

        # self.project_path_ex = r"D:\chris\usd_import_export_maya\tests_exports_temp"
        # self.export_full = f"{self.project_path_ex}\\{self.find_sel()[0]}.usd"
        # print(self.export_full)

        # temp = tempfile.NamedTemporaryFile(prefix = "USD", suffix = ".usd")
        # print(f"\n {temp.name} \n")
        # print(temp)


        #when temp is called, it writes the file, yet the file stays open while we don't tell temp to close it
        #if we don't do so, maya can't edit it and add the usd data to it
        # temp.close()
        cmds.select(selection)

        # we use the officiel export function instead of an export to string because it is easier
        # to export a selection like so. Then we can export the stage to string to apply modifications
        cmds.mayaUSDExport(
            file = export_path,
            selection = True,
            shadingMode = "useRegistry",
        )

        # A ne surtout pas faire, sinon on supprime effectivement le proxy, mais les données usd restent en mémoire dans maya
        # et deviennent inaccessibles.
        "cmds.delete(proxyShapeTest)"

        # os.close(self.export_full)
        # os.remove(self.export_full)

        # temp.close()
        # temp.delete(True)
        print("\n Usd file exported to %s! \n" % export_path)


        # Time to check the file 
        stage = Usd.Stage.Open(export_path)
        # print(stage.GetRootLayer().ExportToString())

        # target_prims = ["/geo", "/mtl"]
        # for prim in stage.Traverse():
        #     if prim.GetTypeName() == "Xform":
        #         prim.SetTypeName("Scope")
        target_prims = ["geo", "mtl"]
        target_prim = [prim for prim in stage.Traverse() if prim.GetName() == "geo"]
        print(target_prim)
        
        target_path = target_prim[0].GetPrimPath()
        start_prim = stage.GetPrimAtPath(target_path)
        iter_prims = iter(Usd.PrimRange(start_prim))
        print("\n")
        target = []
        for prim in iter_prims:
            target.append(prim)
        print(target)
        

        #time for checkings 
        assert len(target) > 2
        if len(target) < 2 :
            print("no prim in /geo") #FIXME

        target_prim[0].SetTypeName("Scope")


        #TODO : Comparer la structure officielle avec la structure sortante
        #TODO: checker les bons types de prim en sortie 



        # print(target_prim[0].split("<", 1))
        # assert len(target_prim) > 0

        # print(stage.GetRootLayer().ExportToString())


if __name__ == "__main__":
    x = create_usd_asset_window()
    x.show()

