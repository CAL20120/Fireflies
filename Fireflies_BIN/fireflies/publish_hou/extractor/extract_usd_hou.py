import pyblish.api
import hou

from fireflies.houdini import abstract_hou_publish


class Usd_Extractor_Hou(pyblish.api.InstancePlugin):
    """Publish usd file from houdini"""

    order = pyblish.api.ExtractorOrder
    optional=False
    label="Publish USD file"

    def __init__(self):
        self.abstract_publish = abstract_hou_publish.hou_publish()


    def process(self, instance):
        node_path = instance.data.get('node')

        self.abstract_publish.extract_usd(node=node_path)
        
