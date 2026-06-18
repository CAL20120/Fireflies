import os
import pyblish.api
import maya.cmds as cmds

from fireflies.context import prod_tracker
CONTEXT = prod_tracker.manage_context()

from fireflies.publish_regular import abstract_publish as ab


class CollectMayaGeometry(pyblish.api.ContextPlugin):
    """Collect all assets in the scene"""

    order = pyblish.api.CollectorOrder - 0.1
    label = "Collect MAYA Data"
    active = True

    def __init__(self):
        pass

    def process(self, context):
        context.data["comment"] = ""

        props_check = False
        rig_check = False

        scene_path = cmds.file(q=True, sn=True).replace('/', '\\')

        CT_PATH = prod_tracker.manage_paths(scene_path)

        os.environ['FIREFLIES_CURRENT_TASK'] = CT_PATH.ct_task


        if 'props' in scene_path.lower():
            props_check = True
            print("### Props check active ###")

        if 'rig' in scene_path.lower():
            rig_check = True
            print("### Rig check active ###")


        context.data['props_check'] = props_check
        context.data['scene_path'] = scene_path
        context.data['rig_check'] = rig_check
        context.data['current_task'] = CT_PATH.ct_task


        target_assets = cmds.ls("*_ASSET", type="transform")
        print(cmds.nodeType(target_assets))
        

        #because the rigs are imported with a special namespace 
        #we need to look for the correct hierarchy
        target_shot_dependencies = cmds.ls("*:*:*_ASSET")

        if target_shot_dependencies:
            shot_out_name = ab.build_shot_name()
            context.data['shot_publish_name'] = shot_out_name


        for asset in target_assets:
            print(asset)

            asset_name = asset.split('|')[-1]

            # asset_name = cmds.listRelatives(asset, children=True)

            if cmds.nodeType(asset) != "transform":
                continue

            instance = context.create_instance(asset_name)
            instance.data["asset_name"] = asset_name

            instance.append("asset_name")
            instance.data["family"] = "assets"


        for asset in target_shot_dependencies: 
            print(asset)

            if cmds.nodeType(asset) != "transform": 
                continue

            asset_parts = asset.split(':')

            asset_name = asset_parts[-1]
            shot_name = asset_parts[0]
                        
            instance = context.create_instance(f"{asset_name} - {CT_PATH.ct_task.upper()}")

            instance.data['asset_name'] = asset_name
            instance.data['shot_name'] = shot_name

            instance.data['maya_namespace'] = asset

            instance.append("asset_name")
            instance.data['family'] = "shot_dependency"



