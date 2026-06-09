import argparse
import os
import sys

import shutil
import time

import hou

from datetime import datetime

def export_usd(scene_path:str, node_path:hou, export_path:str,
               f_start:int, f_end:int, local_scene_path:str, 
               local_usd_path:str):
    
    tmp_dir = os.environ.get('TMP')

    norm_scene = os.path.normpath(scene_path)

    norm_dir = os.path.dirname(norm_scene)
    os.startfile(norm_dir)

    export_dir = os.path.dirname(export_path)
    os.startfile(export_dir)


    farm_dir = os.path.join(os.path.dirname(local_scene_path), 'farm_scenes')

    if not os.path.exists(farm_dir):
        os.makedirs(farm_dir)

    farm_scene_path = os.path.join(
        farm_dir, os.path.basename(local_scene_path)
    ).replace('\\', '/')


    shutil.copyfile(local_scene_path, farm_scene_path)

    local_scene_path = farm_scene_path


    # nas_path = scene_path.replace(os.sep, '/')
    scene_name = os.path.basename(norm_scene)

    nas_export_path = export_path

    export_path = local_usd_path.replace('\\', '/')
    master_path = os.path.join(os.path.dirname(export_path), f'master_anim_{f_start}.usdc')


    try:
        hou.hipFile.load(local_scene_path)

    except:
        time.sleep(60)
        print("### Trying to reload scene ###")
        hou.hipFile.load(local_scene_path)


    print("### Scene loaded at: {} ###".format(local_scene_path))


    nas_dir = os.path.dirname(scene_path)
    hou.hscript(f"set -g HIP = '{nas_dir}'")
    hou.hscript(f"set -g JOB = '{nas_dir}'")


    target_rop = hou.node(f"{node_path}/rop_dd")
    current_network = target_rop.parent()


    if not target_rop: 
        print("### Error - Couldn't find the rop_dd node ###")
        return


    print("Exporting master file")

    target_rop.parm('lopoutput').set(master_path)
    target_rop.parm('trange').set(1)

    target_rop.parm('f1').set(f_start)
    target_rop.parm('f2').set(f_end)

    target_rop.parm('savestyle').set("flattenimplicit")

    target_rop.parm('flattenfilelayers').set(1)
    target_rop.parm('flattensoplayers').set(1)

    target_rop.parm('fileperframe').set(1)

    target_rop.render()

    print("Master Exported")


    print("Exporting sequence")

    master_node = current_network.createNode('sublayer', 'TMP_master')
    master_node.parm('filepath1').set(master_path)

    seq_rop = current_network.createNode('usd_rop', 'TMP_rop_seq')
    seq_rop.setInput(0, master_node)

    seq_rop.parm('lopoutput').set(local_usd_path)
    seq_rop.parm('trange').set(1)

    f1_parm = seq_rop.parm('f1')
    f2_parm = seq_rop.parm('f2')
    
    f1_parm.deleteAllKeyframes()
    f1_parm.set(f_start)

    f2_parm.deleteAllKeyframes()
    f2_parm.set(f_end)

    seq_rop.parm('fileperframe').set(1)

    seq_rop.render()

    master_node.destroy()
    seq_rop.destroy()

    try:
        shutil.copytree(src=os.path.dirname(local_usd_path),  dst=os.path.dirname(nas_export_path),
                        dirs_exist_ok=True)

    except: 
        raise FileExistsError("Couldn't copy the usd files to the server")


    local_usd_dir = os.path.dirname(local_usd_path)

    for file in os.listdir(local_usd_dir):
        if file.endswith('.usdc'):
            os.remove(os.path.join(local_usd_dir, file))


    print("### Fireflies - USD FILES EXPORTED SUCCESSFULLY ###")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-scene_path')
    parser.add_argument('-node_path')
    parser.add_argument('-export_path')
    parser.add_argument('-local_usd_path', type=str)
    parser.add_argument('-local_scene_path')

    parser.add_argument('-f_start', type=int)
    parser.add_argument('-f_end', type=int)

    args = parser.parse_args()

    export_usd(args.scene_path, args.node_path, args.export_path,
               args.f_start, args.f_end, args.local_scene_path,
               args.local_usd_path)


main()