import pyblish.api
import hou
from fireflies.houdini import abstract_hou_publish


class Usd_Extractor_Anim(pyblish.api.InstancePlugin):
    """Publish usd animation from houdini"""

    order = 2.1
    optional=True
    active=False
    
    label="Publish Usd animation from houdini"

    def __init__(self):
        pass

    def process(self, instance):
        prim = instance.data.get('prim')

        publish_node = instance.data.get('node')

        self.abstract_publish = abstract_hou_publish.hou_publish()
        
        node = instance.data.get('node')

        try:
            stage_local_path = self.abstract_publish.extract_animation(root_prim=prim, node=node)
            instance.data['stage_local_path'] = stage_local_path
        
        except pyblish.api.ValidationError: 
            return
        