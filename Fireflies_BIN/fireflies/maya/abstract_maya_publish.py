import sys 
import os 

import subprocess
import re

from datetime import datetime

import json

from fireflies.context import prod_tracker
CONTEXT = prod_tracker.manage_context()

from fireflies.maya import maya_utils

REGULAR_UTILS = maya_utils.maya_regular()
USD_UTILS = maya_utils.maya_usd()

import maya.cmds as cmds #type:ignore 


from pxr import Usd, UsdGeom, UsdShade, UsdUtils #type: ignore 



def get_last_version(asset_name:str, target_export_dir:str=None,
                            is_rig:bool=False):
    """
    Gets the last published version and version number of a given asset
    """

    scene_path = cmds.file(q=True, sn=True)
    scene_dir = os.path.dirname(scene_path)

    out_dir = 'mb_published' if is_rig else 'usd_published'
    target_ext = 'mb' if is_rig else 'usd' 

    publish_dir = os.path.join(scene_dir, out_dir).replace('\\', '/')

    if not os.path.exists(publish_dir):
        os.makedirs(publish_dir)


    version_id = 1
    version_check = True


    if target_export_dir:
        publish_dir = target_export_dir


    while version_check:
        export_dir = f"{publish_dir}/{asset_name}/{asset_name}_{version_id:03}"
        
        exists = os.path.exists(export_dir)
        if not exists:
            os.makedirs(export_dir)
            break
        version_id += 1

    export_path = f"{export_dir}/{asset_name}.{target_ext}"

    return export_dir, export_path



class maya_regular_publish():
    def __init__(self):
        pass
    

    def extract_rig(self, input_path:str, asset_name:str):
        """
        Extract the rig as the maya sceme (simple saving at the output_path and reloading the scene)

        Args:
            input_path(str): The current scene path
            asset_name(str): The targeted asset name
        """

        out_dir, output_path = get_last_version(asset_name=asset_name, is_rig=True)

        cmds.file(rename=output_path)
        cmds.file(save=True)

        cmds.file(input_path, open=True)



    def export_preview(self, asset_name:str) -> str:
        export_dir, target_version = self.get_export_path(asset_name)

        preview_dir = "{}/metadata/preview".format(target_version)

        preview_dir = os.path.join(export_dir, preview_dir)
        preview_path = f"{preview_dir}/{asset_name}_preview.jpg"

        if not os.path.exists(preview_dir):
            os.makedirs(preview_dir)

        f_start = cmds.playbackOptions(q=True, min=True)

        f_range = (f_start, f_start)

        REGULAR_UTILS.create_playblast(output=preview_path, f_range=f_range)
        
        print("### PREVIEW: {} ###".format(preview_path))
        
        return preview_path




class maya_usd_publish():
    def __init__(self):
        pass


    def extract_usd_animation(self, asset_name:str, namespace:str):
        out_usd_hierarchy = namespace.replace(':', '/')

        target_prefix, target_suffix = out_usd_hierarchy.split(asset_name, 1)

        out_suffix = re.sub(r'\d+', '', target_suffix)

        out_usd_hierarchy = f"/{asset_name}" + out_suffix

        print("### Namespace to hierarchy: {} ###".format(out_usd_hierarchy))


        f_start = cmds.playbackOptions(q=True, min=True)
        f_end = cmds.playbackOptions(q=True, max=True)

        f_range = (f_start, f_end)

        export_dir, output_path = get_last_version(asset_name)

        cmds.mayaUSDExport(
            file=output_path,
            stripNamespaces=True, 
            parentScope=out_usd_hierarchy,
            selection=True, 
            shadingMode='none', 
            exportUVs=False, 
            frameRange=f_range
        )
