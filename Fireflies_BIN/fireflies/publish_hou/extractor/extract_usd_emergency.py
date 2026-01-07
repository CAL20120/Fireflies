import pyblish.api 
import hou 

from fireflies.houdini import abstract_hou_publish

class Usd_Emergency_Extract(pyblish.api.InstancePlugin):
        """Emergency (debug) usd publishing"""

        order = 2.5
        optional=True
        active=False

        label="Emergency Publish"

        def __init__(self):
            self.abstract_publish = abstract_hou_publish.hou_publish()

        def process(self, instance):
            node = instance.data.get('node')

            prim = instance.data.get('prim')

            self.abstract_publish.debug_export(root_prim=prim, node=node)