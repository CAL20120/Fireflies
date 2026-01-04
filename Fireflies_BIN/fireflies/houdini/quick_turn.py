import os
import sys

import re
import argparse

import subprocess

import hou


from fireflies.houdini import deadline_hou_submitter, hou_utils

HYTHON_PATH = "C:\\Fireflies\\Fireflies_BIN\\Sidefx\\env\\deadline_hython_310.bat"


def quick_turn(scene_path:str, node_path:hou) -> hou:
    hou.hipFile.load(scene_path)

    current_node = hou.node(node_path)

    asset_name = current_node.evalParm('asset_name')

    if not asset_name:
        print("### No asset name was found -- Exiting ###")
        return

    machine_sel = current_node.evalParm('dl_machine_list')

    target_machine = False
    if machine_sel:
        target_machine = True

    dl_turn_priority = current_node.evalParm('dl_priority')

    dl_turn_comment = ""
    comment_parm = current_node.evalParm('dl_comment')
    if comment_parm:
        dl_turn_comment = comment_parm


    scene_dir = os.path.split(scene_path)[0]

    target_dir_name = f"{asset_name}_turn"

    export_dir = os.path.join(scene_dir, target_dir_name)

    if not os.path.exists(export_dir):
        os.makedirs(export_dir)


    stage_export_path = os.path.join(export_dir, "prep_turn_{}.usd".format(asset_name))

    stage = current_node.stage()
    stage.Export(stage_export_path)

    hou.hipFile.clear()

    new_scene = os.path.join(export_dir, "{}_quick_turn.hipnc".format(asset_name))

    hou.hipFile.save(new_scene)

    f_start = 1001
    f_end = 1046

    hou.playbar.setFrameRange(f_start, f_end)
    hou.playbar.setPlaybackRange(f_start, f_end)


    init_node = hou.node('/obj')
    lop_node = init_node.createNode("lopnet", "turntable")

    sublayer_node = lop_node.createNode("sublayer", "turn_usd")
    sublayer_node.parm('filepath1').set(stage_export_path)

    transform_node = lop_node.createNode("xform", "roty")
    transform_node.setInput(0, sublayer_node)

    transform_node.parm('primpattern').set('%type:Mesh')

    target_roty = transform_node.parm('ry')
    f_key = hou.Keyframe()

    f_key.setFrame(f_start)
    f_key.setValue(0)
    target_roty.setKeyframe(f_key)

    f_key.setFrame(f_end)
    f_key.setValue(360)
    target_roty.setKeyframe(f_key)


    hdri_path = "Z:/VFX_LIB/04_LIGHTING/HDRI/studio_small_09_4k_LIGHT.tex"

    light_node = lop_node.createNode("domelight::3.0", "turn_hdri")
    light_node.parm('xn__inputstexturefile_r3ah').set(hdri_path)
    light_node.setInput(0, transform_node)


    render_node = lop_node.createNode("fireflies_rm_render", "render_turn")
    render_node.setInput(0, light_node)

    render_node.parm('cam').set('/cam_turn')
    render_node.parm('trange').set(1)
    
    export_path = f"{asset_name}_turn_images\\{asset_name}_turn_$F.exr"
    out_images = os.path.join(export_dir, export_path)

    if not os.path.exists(os.path.dirname(out_images)):
        os.makedirs(os.path.dirname(out_images))

    out_images = out_images.replace(os.sep, '/')

    utils = hou_utils.hou_usd()

    out_images = utils.path_converter(out_images)

    render_node.parm('unlock_path').set(1)
    render_node.parm('output').set(out_images)

    render_node.parm('dl_priority').set(dl_turn_priority)
    render_node.parm('dl_comment').set(dl_turn_comment)
    

    if target_machine:
        render_node.parm('dl_machine_sel').set(1)
        render_node.parm('dl_machine_list').set(machine_sel)


    render_node.cook(force=True)

    sumbit_parm = render_node.parm('dl_sumbit')
    sumbit_parm.pressButton()


def launch_turn_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-scene_path', type=str)
    parser.add_argument('-node_path', type=str)

    args = parser.parse_args()

    quick_turn(args.scene_path, args.node_path)



#we need those args because in the future we may want this script to be executed as standalone
#here we call main() from houdini so we need to bring the args to call launch_turn_args()

def main(scene_path:str, node_path:str):
    script_path = r"C:\Fireflies\Fireflies_BIN\fireflies\houdini\quick_turn.py"

    scene_path = os.path.normpath(scene_path)
    print(scene_path)
    print(node_path)

    cmd = f"{HYTHON_PATH} {script_path} -scene_path {scene_path} -node_path {node_path}"

    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
    )

    stdout, stderr = proc.communicate()
    print(stdout)
    print(stderr)



if __name__ == "__main__":
    launch_turn_args()