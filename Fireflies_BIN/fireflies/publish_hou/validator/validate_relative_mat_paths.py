import pyblish.api 

import hou
import os

from fireflies.houdini import abstract_hou_publish

class Usd_Validator_Hou(pyblish.api.InstancePlugin):
    """Conform texture paths"""

    order = 2.8
    optional = True
    label = "Convert texture paths"


    def process(self, instance):
        self.abstract_publish = abstract_hou_publish.hou_publish()

        # node = instance.data.get('node')
        # current_layer = instance.data.get('current_layer')
        current_scene = hou.hipFile.path()

        if "assembly" in os.path.dirname(current_scene):
            return
        
        stage_path = instance.data.get('stage_local_path')
        print(stage_path)


        self.abstract_publish.resolve_relative_paths(stage_path=stage_path)
