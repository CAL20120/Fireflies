import pyblish.api
import hou
import os

from fireflies.houdini import abstract_hou_publish

class Usd_Extractor_Hou(pyblish.api.InstancePlugin):
    """Publish usd file from houdini"""

    # order = pyblish.api.ExtractorOrder
    order = 1.1
    optional=True
    label="Publish USD file (single frame)"



    def process(self, instance):
        self.abstract_publish = abstract_hou_publish.hou_publish()

        node = instance.data.get('node')
        # self.abstract_publish.extract_usd(node=node_path)

        prim_path = instance.data.get('prim_path') 
        prim = instance.data.get('prim')

        current_scene = hou.hipFile.path()

        if "assembly" in os.path.dirname(current_scene):
            self.abstract_publish.export_full_scene(asset_name=instance.name, current_node=node)

        else:
            self.abstract_publish.extract_usd(root_prim=prim)

