import os
import sys

from fireflies.houdini import hou_utils

import hou

class hou_publish():
    def __init__(self):
        super(hou_publish, self).__init__()

        self.utils = hou_utils.hou_usd()
        self.curr_context = self.utils.get_current_context()
        self.scene_path = hou.hipFile.path().rsplit("/", 1)[0]

        self.export_dir = f"{self.scene_path}/usd_published"

    def fetch_targets(self):
        #in houdini, we have a special parameter "publish" on nulls that defines wich are the targeted publishable assets

        print(self.curr_context)

        target_nodes = []
        target_paths = []

        for node in self.curr_context.allSubChildren():
            target_parm = node.parm('target_publish')
            if target_parm:
                target_nodes.append(node.name())
                target_paths.append(node.path())
        
        print(zip(target_nodes, target_paths))

        return target_nodes, target_paths


    def extract_usd(self, node):

        stage = node.stage()

        asset_name = node.evalParm('asset_name')
        export_path = "{}/{}.usd".format(self.export_dir, asset_name)

        if not os.path.exists(self.export_dir):
            os.makedirs(self.export_dir)

        stage.Export(export_path)

    def write_commentary(self, text, asset_name):
        comment_dir = "{}/metadata/commentary".format(self.export_dir)
        comment_path = f"{comment_dir}/{asset_name}_comment.txt"

        if not os.path.exists(comment_dir):
            os.makedirs(comment_dir)

        with open(comment_path, "w") as f:
            f.write(text)
