from fireflies.context import prod_tracker
from fireflies.context.prod_tracker import CT_HOU, CT_MAYA, CT_NUKE

CONTEXT = prod_tracker.manage_context()

import os
import sys

import json
import subprocess

import re

from datetime import datetime


if CT_MAYA:
    import maya.cmds as cmds
    from fireflies.maya import maya_utils
    M_UTILS = maya_utils.maya_regular()

if CT_HOU:
    import hou
    from fireflies.houdini import hou_utils
    UTILS = hou_utils.hou_usd()



def get_export_path(asset_name, is_rig:bool=False):
    scene_path = prod_tracker.get_scene_path()

    scene_dir = os.path.dirname(scene_path)

    out_dir = 'mb_published' if is_rig else 'usd_published'
    target_ext = 'mb' if is_rig else 'usd' 

    publish_dir = os.path.join(scene_dir, out_dir).replace('\\', '/')

    versions_dir = os.path.join(publish_dir, asset_name)

    export_dir = versions_dir

    target_versions = sorted(
        [d for d in os.listdir(export_dir) if os.path.isdir(os.path.join(export_dir, d))]
    )

    print(target_versions)

    target = re.search(r'(\d+)$', target_versions[-1])
    result = int(target.group())

    #I had to change the execution order of the pyblish extractors
    #So the different tasks wouldn't create different versions
    # result += 1

    target_version = f"{asset_name}_{int(result):03d}"

    return export_dir, target_version



def write_commentary(text, asset_name):
    scene_path = prod_tracker.get_scene_path()
    
    if 'rig' in scene_path and CT_MAYA:
        export_dir, target_version = get_export_path(asset_name, is_rig=True)

    else:
        export_dir, target_version = get_export_path(asset_name=asset_name)

    comment_dir = "{}/metadata/commentary".format(target_version)
    comment_dir = os.path.join(export_dir, comment_dir)

    comment_path = f"{comment_dir}/{asset_name}_comment.txt"

    print(comment_path)

    if not os.path.exists(comment_dir):
        os.makedirs(comment_dir)

    with open(comment_path, "w") as f:
        f.write(text)




def batch_kt_preview(scene_path:str):
    """
    Quick method to let create a preview and send it to kitsu without the publisher \n
    with the metadata pipeline integration
    """
    
    props_check = False
    if 'props' in scene_path.lower():
        props_check = True

    print(f"props check : {props_check}")

    scene_name = os.path.basename(os.path.splitext(scene_path)[0])

    if CT_HOU:
        output = f"{os.path.dirname(scene_path)}/quick_preview/{scene_name}_$F4.jpg"

    if CT_MAYA:
        output = f"{os.path.dirname(scene_path)}/quick_preview/preview_####.jpg"


    preview_path = export_video_preview(asset_name=scene_name, scene_path=scene_path,
                                            is_asset=props_check, export_path=output)


    print("### Sending preview to kitsu... ###")

    comment = "Fireflies - Preview Published"

    if props_check:
        ct_scene = prod_tracker.manage_paths(scene_path, is_asset=True)
        asset_name = f"{ct_scene.ct_name}_ASSET"
        print(asset_name)

        CONTEXT.publish_asset_task(asset_name=asset_name, scene_path=scene_path,
                                    preview_path=preview_path, comment=comment)
        
        print("### PREVIEW SENT TO KITSU ###")
        return

    CONTEXT.publish_shot_task(preview_path=preview_path, scene_path=scene_path, 
                                comment=comment)

    print("### PREVIEW SENT TO KITSU ###")



def export_video_preview(asset_name, scene_path=None,
                            is_asset:bool=False, export_path:str=None):
    
    if not export_path:
        export_dir, target_version = get_export_path(asset_name)

        preview_dir = "{}/metadata/video_preview".format(target_version)
        out_dir = os.path.join(export_dir, preview_dir)

        if CT_HOU:
            preview_path = f"{out_dir}/{asset_name}_preview_$F4.jpg"
        
        if CT_MAYA:
            preview_path = f"{out_dir}/{asset_name}_preview_####.jpg"


    else:
        preview_path = export_path
        out_dir = os.path.dirname(preview_path)

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)


    if CT_HOU:
        f_start, f_end = hou.playbar.playbackRange()
        frame_range = (int(f_start), int(f_end))

        UTILS.create_playblast(preview_path, frame_range)

    if CT_MAYA:
        f_start = int(cmds.playbackOptions(q=True, min=True))
        f_end = int(cmds.playbackOptions(q=True, max=True))

        frame_range = (f_start, f_end)

        M_UTILS.create_playblast(f_range=frame_range, output_path=preview_path)


    print("### Playblast Done ###")

    kt_infos = None
    if scene_path:
        if is_asset:
            kt_infos = CONTEXT.get_full_ct(scene_path, asset=True)
        
        else:
            kt_infos = CONTEXT.get_full_ct(scene_path)
        
        print("### Fetched kt infos for preview ###")

        #we need to convert the dict to pass it to argparse
        kt_infos_json = json.dumps(kt_infos)
        # kt_infos_json = kt_infos_json.replace('""', '\\"')

        kt_infos = kt_infos_json

        print("### KT INFO converted to json schema ###")

        kt_user = CONTEXT.kt_user['full_name'].split(' ')[0]

        general_infos = {
            'scene_name': os.path.splitext(os.path.basename(scene_path))[0], 
            'time': str(datetime.now())
        }

        general_infos_json = json.dumps(general_infos)
        general_infos_json = general_infos_json.replace('""', '\\"')


    if CT_HOU:
        first_frame = preview_path.replace('$F4', str(frame_range[0]))
    
    if CT_MAYA:
        first_frame = preview_path.replace('####', str(frame_range[0]))
        
    print(first_frame)


    local_appdata = os.environ.get('LOCALAPPDATA')

    script_path = "C:\\Fireflies\\Fireflies_BIN\\fireflies\\fireflies_utils\\video_converter.py"
    python_path = f"{local_appdata}\\Programs\\Python\\Python310\\python.exe"

    #otherwise houdini with launch the process with hython
    proc_env = os.environ.copy()
    proc_env.pop("PYTHONPATH", None)
    proc_env.pop("PYTHONHOME", None)

    proc_cmd = [
        python_path, script_path, '-first_image_path', first_frame, 
        '-kt_infos', kt_infos, '-user', kt_user, '-general_infos', general_infos_json
    ]

    print(proc_cmd)

    proc = subprocess.Popen(
        proc_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=proc_env
    )

    stdout, stderr = proc.communicate()

    print(stdout)
    print("##############")
    print(stderr)


    print("### Preview video generated ###")

    preview_full_path = os.path.join(out_dir.replace('/', '\\'), 'video_preview.mp4')
    # preview_full_path = os.path.join(export_dir.replace('/', '\\'), out_video_path)
    
    print("### out video: {} ###".format(preview_full_path))

    if not os.path.exists(preview_full_path):
        raise FileExistsError("### Couldn't find the video preview -- Exiting ###")

    return preview_full_path



def export_preview(asset_name:str) -> str:
    export_dir, target_version = get_export_path(asset_name)

    preview_dir = "{}/metadata/preview".format(target_version)

    preview_dir = os.path.join(export_dir, preview_dir)
    preview_path = f"{preview_dir}/{asset_name}_preview.jpg"

    if not os.path.exists(preview_dir):
        os.makedirs(preview_dir)

    f_start = cmds.playbackOptions(q=True, min=True)

    f_range = (f_start, f_start)

    M_UTILS.create_playblast(f_range=f_range, output_path=preview_path)
    
    print("### PREVIEW: {} ###".format(preview_path))
    
    return preview_path



def build_shot_name(scene_path:str=None):
    """
    Used to build the asset name of a shot to verify the nomenclature 
    when publishing
    """
    
    if not scene_path:
        scene_path = prod_tracker.get_scene_path()

    curr_context = CONTEXT.get_full_ct(scene_path)

    if curr_context['is_asset']: 
        raise Exception(
            "### Cannot get a shot name within an asset context ###"
        )
        
    
    curr_entity = curr_context['current_entity']
    shot_name = curr_entity['name']
    sequence_name = curr_entity['sequence_name']

    out_shot_name = f"_{sequence_name}_{shot_name}_SHOT"

    return out_shot_name
