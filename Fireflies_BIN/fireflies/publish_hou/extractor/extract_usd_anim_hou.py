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


        self.abstract_publish = abstract_hou_publish.hou_publish()
        
        node = instance.data.get('node')

        self.abstract_publish.extract_animation(root_prim=prim, node=node)