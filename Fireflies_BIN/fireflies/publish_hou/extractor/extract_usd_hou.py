import pyblish.api
import hou

from fireflies.houdini import abstract_hou_publish

class Usd_Extractor_Hou(pyblish.api.InstancePlugin):
    """Publish usd file from houdini"""

    # order = pyblish.api.ExtractorOrder
    order = 1.1
    optional=True
    label="Publish USD file (single frame)"



    def process(self, instance):
        self.abstract_publish = abstract_hou_publish.hou_publish()

        # node_path = instance.data.get('node')
        # self.abstract_publish.extract_usd(node=node_path)

        prim_path = instance.data.get('prim_path') 
        prim = instance.data.get('prim')

        self.abstract_publish.extract_usd(root_prim=prim)

