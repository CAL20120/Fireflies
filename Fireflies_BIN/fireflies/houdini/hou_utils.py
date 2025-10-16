#This file contains all the classes and methods often used when interacting with houdini hou module in usd
import hou
import os
class hou_usd():
    def __init__(self):
        self.scene_path = hou.hipFile.path().rsplit("/", 1)[0]
        self.scene_name = self.scene_path.rsplit("/")[-1]
        self.prod_name = hou.hipFile.path().rsplit("/")[-5]

    def import_prod_usd_asset(self, asset_path):

        asset_name = asset_path.rsplit("/", 1)[-1].split(".", 1)[0]

        #we need to get the current context path to create the node that will reference our 
        #target asset
        desktop = hou.ui.curDesktop()
        pane = desktop.paneTabOfType(hou.paneTabType.NetworkEditor)
        curr_context = pane.pwd()

        asset_node = curr_context.createNode("assetreference", asset_name)
        node_path = hou.node(asset_node.path())

        node_path.parm('filepath').set(asset_path)

    def build_render_path(self, version):
        
        export_dir = f"{self.scene_path}/render_{self.prod_name}/{self.prod_name}_{version}"
        export_path = f"{export_dir}/{self.prod_name}_{version}_render_$F4.exr"

        if not os.path.exists(export_dir):
            os.makedirs(export_dir)

        return export_path