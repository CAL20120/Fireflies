import os
import sys

import subprocess


from fireflies.context import prod_tracker
CONTEXT = prod_tracker.manage_context()


import maya.cmds as cmds #type:ignore 

class maya_usd():
    def __init__(self):
        pass


    def import_usd_asset(self, asset_path:str):
        cmds.mayaUSDImport(
            file = asset_path, 
            primPath = "/", 
            importInstances= True, 
            excludePrimvar = "None"
        )

        asset_name = os.path.basename(asset_path)[-4:]
        print(asset_name)

        maya_transform = cmds.createNode("transform", name=asset_name)
        maya_proxyShape = cmds.createNode("mayaUsdProxyShape", name=f"{asset_name}_UsdShape", parent=maya_transform)

        cmds.setAttr(f"{maya_proxyShape}.filePath", asset_path, type="string")

        print("### Asset Imported: {} ###".format(asset_name))



    def import_usd_animation(self):
        pass


    def import_maya_rig(self):
        pass



class maya_regular():
    def __init__(self):
        pass