import os 
import pyblish.api 

import hou 

from fireflies.context import prod_tracker
from fireflies.houdini import hou_utils, abstract_hou_publish

class CollectHouData(pyblish.api.ContextPlugin):
    """Collect Any Assets, Layouts or pyblishable data  from houdini"""

    order = pyblish.api.CollectorOrder - 0.1
    label = "Collect Hou DATA"
    version = (0, 0, 1)
    active = True

    def __init__(self):
        super(CollectHouData, self).__init__()
        self.x = hou_utils.hou_usd()
        self.curr_context = self.x.get_current_context()

        self.abstract_publish = abstract_hou_publish.hou_publish()

    def process(self, context):
        context.data["comment"] = ""
        
        props_check = False
        
        if prod_tracker.CT_HOU:
            print("CT HOU ON PUBLISH")
            scene_path = hou.hipFile.path().replace('/', '\\')

        if 'props' in scene_path:
            props_check = True
            print("### Props check active ###")

        context.data['props_check'] = props_check
        context.data['scene_path'] = scene_path

        targets, paths, prim, nodes = self.abstract_publish.fetch_targets()

        for index, name in enumerate(targets):
            instance = context.create_instance(name)
            instance.data['prim_path'] = paths[index]
            instance.data['prim'] = prim[index]
            instance.data['node'] = nodes[index]

            # instance.append("node")
            instance.data['family'] = "assets"
