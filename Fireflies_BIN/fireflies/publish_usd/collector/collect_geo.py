import os
import pyblish.api
import maya.cmds as cmds

class CollectMayaGeometry(pyblish.api.ContextPlugin):
    """Collect all geo in the scene"""

    order = pyblish.api.CollectorOrder - 0.5
    label = "Collect Geometry"
    version = (1, 0, 0)

    active = True

    def process(self, context):
        # list all groups that have a subgoup called "geo

        asset_candidates = cmds.ls("*_ASSET", type="transform")
        print(cmds.nodeType(asset_candidates))
        for asset_candidate in asset_candidates:
            print(asset_candidate)
            #if we use the first xform in the hierarchy it returns None if we get the children here
            asset_name = cmds.listRelatives(asset_candidate, children=True)
            # asset_name = asset_candidates
            if cmds.nodeType(asset_candidate) != "transform":
                continue
            instance = context.create_instance(asset_candidate)
            # instance = pyblish.api.Instance(name="MAYA_USD")
            instance.data["asset_name"] = asset_candidate
            instance.append("asset_name")
            instance.data["family"] = "geometry"

            instance[0] = asset_candidate
