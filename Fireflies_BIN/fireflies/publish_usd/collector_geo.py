import pyblish.api 
import maya.cmds as cmds 

import os

class CollectorAssetsMaya(pyblish.api.ContextPlugin):
    """Collect _Assets in scene"""

    order = pyblish.api.CollectorOrder - 0.5
    label = "Maya Geometry _ASSET"
    hosts = ["maya"]
    version = (0, 1, 0)

    active = True

    def process(self, context):
        asset_candidates = cmds.ls("*_ASSET", type="transform")

        for asset_candidate in asset_candidates:
            asset_name = cmds.listRelatives(asset_candidate, children=True)
            if cmds.nodeType(asset_candidate) != "transform":
                return

            instance = context.create_instance(asset_candidate)
            instance.data["asset_name"] = asset_candidate
            instance.append("asset_name")
            instance[0] = asset_candidate

            for instance in context:
                self.log.debug(str(instance))