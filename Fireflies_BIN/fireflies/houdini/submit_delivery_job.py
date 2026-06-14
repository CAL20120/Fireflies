import hou

import os
import sys

import argparse
import json

from fireflies.houdini import hou_utils

def launch_delivery(scene_path, render_settings, validate_path):
    print("### Creating delivery scene ###")
    
    print(scene_path)

    if os.path.exists(scene_path):
        os.remove(scene_path)


    hou.hipFile.save(file_name=scene_path)

    UTILS = hou_utils.hou_usd()


    with open(render_settings, 'r') as f:
        render_settings_dict = json.load(f)

    f_start = render_settings_dict['f1']
    f_end = render_settings_dict['f2']

    hou.playbar.setFrameRange(f_start, f_end)
    hou.playbar.setPlaybackRange(f_start, f_end)

    init_node = hou.node('/obj')
    lop_node = init_node.createNode("lopnet", "delivery_setup")


    valid_ref_node = lop_node.createNode("reference", "validate_ref")

    valid_hip_path = UTILS.path_converter(validate_path)
    valid_ref_node.parm('filepath1').set(valid_hip_path)


    render_node = lop_node.createNode('fireflies_rm_render', 'render_validate')
    render_node_path = render_node.path()
    render_node.setInput(0, valid_ref_node)


    hou_utils.load_preset(render_node_path, render_settings)

    output_parm = render_node.parm('output')
    render_path = output_parm.unexpandedString()

    if os.path.isabs(render_path):
        render_hip_path = UTILS.path_converter(render_path)

    output_parm.set(render_hip_path)


    hou.hipFile.save(file_name=scene_path)

    print("### SCENE SET ###")

    sumbit_parm = render_node.parm('dl_sumbit')
    sumbit_parm.pressButton()

    sys.exit(0)


if __name__ == "__main__": 
    parser = argparse.ArgumentParser()
    parser.add_argument('-scene_path', type=str)
    parser.add_argument('-render_path', type=str)
    parser.add_argument('-render_settings', type=str)
    parser.add_argument('-validate_path', type=str)

    args = parser.parse_args()

    launch_delivery(args.scene_path, args.render_settings, args.validate_path)