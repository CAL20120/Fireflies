import os
import maya.cmds as cmds 
import maya.mel as mel 

import tempfile

import mayaUsd
import mayaUsdCacheMayaReference
from mayaUsdLibRegisterStrings import getMayaUsdLibString
import mayaUsd.ufe
import mayaUsdMergeToUsd
import mayaUsd.lib as UsdLib

import ufe 
import mayaUsdOptions

from pxr import Usd, Sdf

from functools import partial


class maya_to_usd():
    def __init__(self):
        super(maya_to_usd, self).__init__()
        self.export_path = r"D:\chris\asset_checker\test_scenes\usd_sphere_sample.usda"
        self.export_dir = r"D:\chris\asset_checker\test_scenes\temp"

    def check_exists(self):
        if os.path.exists(self.export_path):
            return True
        else: 
            return False

    def find_sel(self) -> list:
        sel = cmds.ls(sl=True)
        mesh = sel[0]
        return mesh

    def converter(self):
        anon = Sdf.Layer.CreateAnonymous("test")
        proxyShape = cmds.createNode('mayaUsdProxyShape', skipSelect=True, name= f"{self.find_sel()}_asset")
        # print(cmds.ls(type = "mayaUsdProxyShape"))
        cmds.select(proxyShape, replace=True)
        fullPath = cmds.ls(proxyShape, long=True)
        
        # stage = Usd.Stage.Open(r'')
        # stage.GetRootLayer().ExportToString()
        return fullPath[0]

    def test_anon(self, extension) -> Usd:

        self.proxyShape = cmds.createNode('mayaUsdProxyShape', skipSelect=True, name= f"{self.find_sel()}_asset")
        layer = Sdf.Layer.CreateAnonymous("test")
        stage = Usd.Stage.Open(layer)
        prim01 = stage.DefinePrim(f"/{self.find_sel()}_mesh", "xform")
        prim01.SetTypeName("Xform")


        initial_obj = self.find_sel()
        target = cmds.listRelatives(initial_obj, allDescendents = True)

        ## FIXME : prendre à la base uniquement les objets contenant "_GEO"
        target_obj = [obj for obj in initial_obj if obj.endswith("_GEO")]


        #now we can transfer the data that was sent to the usd layer, to the visible stage in maya
        UsdLib.GetPrim(self.proxyShape).GetStage().GetRootLayer().TransferContent(layer)
        print(layer.identifier)

        # test export temp
        _, temp = tempfile.mkstemp(suffix=".usda", dir=self.export_dir)
        final = stage.GetRootLayer().ExportToString()
        with open(temp, "w") as f:
            f.write(final)
        print(temp)


    def test_export(self) -> Usd:

        # if self.check_exists() == True:
        #     return

        initial_sel = (cmds.ls(sl = True))
        family_sel = cmds.listRelatives(initial_sel, fullPath=True)

        sel_name = cmds.ls(sl = True)[0]
        layer = Sdf.Layer.CreateAnonymous("test relatives")

        #time to convert the maya data into usd
        stage = Usd.Stage.Open(layer)

        cmds.select(family_sel)
        print(family_sel)

        ## export path 
        _, temp = tempfile.mkstemp(suffix = ".usda")
        print(temp)

        cmds.mayaUSDExport(
            file = temp,
            selection = True,
            convertMaterialsTo = "UsdPreviewSurface",
            shadingMode = "useRegistry",
            # rootPrim = f"{sel_name}_root",
        )


        print("\n Usd file exported to %s! \n" % self.export_dir)

        transform = cmds.createNode("transform", name = f"{self.export_path}")
        proxyShapeTest = cmds.createNode('mayaUsdProxyShape', name = "%s_ProxyShape" % sel_name, parent = transform)

        #we need to attribute the layer to the new proxyShape
        cmds.setAttr(f"{proxyShapeTest}.filePath", self.export_path, type = "string")


    def test_temp(self):
        _, temp = tempfile.mkstemp(suffix = ".usda")
        print(temp)


    #TODO : créer une méthode pour updater le layer existant avant l'envoi

    # def update_layer(self):

test = maya_to_usd()

def main():
    # test.test_export()
    test.test_export()

if __name__ == "__main__":
    main()