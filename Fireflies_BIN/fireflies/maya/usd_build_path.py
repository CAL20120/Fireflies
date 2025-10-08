import os
import maya.cmds as cmds 
import maya.mel as mel 

import mayaUsd
from pxr import Usd, Sdf

import pyblish.api 


class maya_to_usd(pyblish.api.ContextPlugin):

    def __init__(self, asset_name):
        super(maya_to_usd, self).__init__()
        self.shot_path = cmds.file(q=True, sn=True).rsplit("/", 1)[0]

        self.asset_name = asset_name

        self.export_path = f"{self.shot_path}/usd_published/{self.asset_name}.usd"
        self.tmp_check_path = f"{self.shot_path}/tmp_check/{self.asset_name}.usda"

        self.root_prim = f"/{self.asset_name}"



    def export_usd(self) -> mayaUsd:

        # cmds.mayaUSDExport(
        #     file = self.export_path,
        #     selection = True,
        #     shadingMode = "useRegistry"
        # )

        transform = cmds.createNode("transform", name = f"{self.asset_name}")
        proxyShapeTest = cmds.createNode('mayaUsdProxyShape', name = "%s_ProxyShape" % self.asset_name, parent = transform)

        #we need to attribute the layer to the new proxyShape
        cmds.setAttr(f"{proxyShapeTest}.filePath", self.export_path, type = "string")


        # A ne surtout pas faire, sinon on supprime effectivement le proxy, mais les données usd restent en mémoire dans maya
        # et deviennent inaccessibles.
        "cmds.delete(proxyShapeTest)"


    def usd_tmp_export(self):
        cmds.select(cmds.listRelatives(self.asset_name, fullPath = True))
        cmds.mayaUSDExport(
            file = self.tmp_check_path,
            selection=True,
        )

        print("temp file exported to %s" % self.tmp_check_path)
        pass


    def publish_usd(self) -> Usd:

        if os.path.exists(self.tmp_check_path):
            # stage = Usd.Stage.Open(self.tmp_check_path)
            print("tmp file found")
            pass
        else:
            print("creating tmp file")
            self.usd_tmp_export()

        stage = Usd.Stage.Open(self.tmp_check_path)

        mtl_init_path = Sdf.Path(f"/{self.asset_name}/mtl")
        print(f"{mtl_init_path}")

        mtl_init_prim = stage.GetPrimAtPath(mtl_init_path)
        mtl_children = mtl_init_prim.GetChildren()

        for children in mtl_children:
            print(type(children))
            stage.RemovePrim(children.GetPath())

        stage.GetRootLayer().Save()
        output_str = stage.GetRootLayer().ExportToString() #temporary 
        stage.Export(self.export_path)

        print(os.path.isfile(self.tmp_check_path))
        os.remove(self.tmp_check_path)
        # with open(self.export_path, "w") as file:
        #     file.write(output)




if __name__ == "__main__":
    x = maya_to_usd()
    x.build_path_ft()


