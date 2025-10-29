import os 
import pyblish.api 

import hou 

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
        
        targets, paths = self.abstract_publish.fetch_targets()

        for name, path in zip(targets, paths):
            node = hou.node(path)

            instance = context.create_instance(node.evalParm('asset_name'))
            instance.data['node'] = hou.node(path)

            # instance.append("node")
            instance.data['family'] = "assets"
