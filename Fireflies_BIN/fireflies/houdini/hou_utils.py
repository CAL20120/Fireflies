#This file contains all the classes and methods often used when interacting with houdini hou module in usd

class hou_usd():
    def __init__(self):
        pass

    def import_prod_usd_asset(self, asset_path):
        import hou

        asset_name = asset_path.rsplit("/", 1)[-1].split(".", 1)[0]

        #we need to get the current context path to create the node that will reference our 
        #target asset
        desktop = hou.ui.curDesktop()
        pane = desktop.paneTabOfType(hou.paneTabType.NetworkEditor)
        curr_context = pane.pwd()

        asset_node = curr_context.createNode("assetreference", asset_name)
        node_path = hou.node(asset_node.path())

        node_path.parm('filepath').set(asset_path)

