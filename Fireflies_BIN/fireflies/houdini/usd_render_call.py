import argparse
import os
import sys
import subprocess

import shutil
import time

import hou

from datetime import datetime

from fireflies.context import prod_tracker


def export_usd(scene_path:str, node_path:hou, export_path:str,
               f_start:int, f_end:int):
    

    local_prod_dir = prod_tracker.get_local_prod_path()
    print("### LOCAL PROD DIR {} ###".format(local_prod_dir))

    nas_export_path = export_path

    norm_scene = os.path.normpath(scene_path)

    norm_dir = os.path.dirname(norm_scene)
    # os.startfile(norm_dir)

    export_dir = os.path.dirname(export_path).replace('\\', '/')
    # os.startfile(export_dir)


    local_scene_path = os.path.join(local_prod_dir, scene_path.split('PRODS')[-1].lstrip('/'))
    print("### LOCAL SCENE PATH: {} ###".format(local_scene_path))

    original_scene = local_scene_path

    local_scene_dir = os.path.dirname(local_scene_path)
    print(local_scene_dir)


    local_basename = os.path.basename(local_scene_path)

    render_path_stem = export_dir.split('PRODS')[-1].lstrip('/')
    
    print(render_path_stem)

    local_usd_path = os.path.normpath(
        os.path.join(local_prod_dir, render_path_stem, '__render__.$F4.usd')
    ).replace('\\', '/')


    farm_dir = os.path.join(os.path.dirname(local_scene_path), 'farm_scenes')

    if not os.path.exists(farm_dir):
        os.makedirs(farm_dir)

    farm_scene_path = os.path.join(
        farm_dir, os.path.basename(local_scene_path)
    ).replace('\\', '/')


    shutil.copyfile(local_scene_path, farm_scene_path)

    local_scene_path = farm_scene_path

    master_path = os.path.join(
        os.path.dirname(local_usd_path), f'master_anim_{f_start}.usd'
    ).replace('\\', '/')


    try:
        hou.hipFile.load(local_scene_path)

    except:
        raise FileExistsError("### Couldn't load the houdini scene file at: {} ###".format(local_scene_path))

    print("### Scene loaded at: {} ###".format(local_scene_path))


    hip_dir = os.path.dirname(original_scene)
    hou.hscript(f"set -g HIP = '{hip_dir}'")
    hou.hscript(f"set -g JOB = '{hip_dir}'")


    render_node = hou.node(node_path)
    render_node.allowEditingOfContents()

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

    print("### EXPORTING MASTER TO: {} ###".format(master_path))

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

    # try:
    #     shutil.copytree(src=os.path.dirname(local_usd_path),  dst=os.path.dirname(nas_export_path),
    #                     dirs_exist_ok=True, copy_function=shutil.copy)

    # except: 
    #     raise FileExistsError("Couldn't copy the usd files to the server")


    # local_usd_dir = os.path.dirname(local_usd_path)

    # for file in os.listdir(local_usd_dir):
    #     if file.endswith('.usdc'):
    #         os.remove(os.path.join(local_usd_dir, file))


    print("### Fireflies - USD FILES EXPORTED SUCCESSFULLY ###")



def render_usd_local(usd_path, out_images, delegate:str, frame:str, husk_path:str):
    local_prod_dir = prod_tracker.get_local_prod_path().replace('\\', '/')

    rel_path = usd_path.split('PRODS', 1)[-1].lstrip('/\\')
    local_usd = os.path.join(local_prod_dir, rel_path).replace('\\', '/')

    print("### LOCAL USD: {} ###".format(local_usd))


    elapsed = 0
    wait_interval = 10

    while not os.path.exists(local_usd):
        if elapsed >= 500:
            print("### Couldn't find the USDC render file - TIMEOUT ###")
            sys.exit(1)

        print("### Waiting for usdc render file... ###")
        time.sleep(wait_interval)
        elapsed += wait_interval

    print("### USDC FILE FOUND ###")


    args = f'{husk_path} -R {delegate} -V 3 --exrmode 1 -s /Render/rendersettings -o {out_images} {local_usd} --frame {str(frame)}'

    proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    stdout, stderr = proc.communicate()
    print(stdout, stderr)

    if proc.returncode != 0: 
        sys.exit(proc.returncode)




def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-scene_path')
    parser.add_argument('-node_path')
    parser.add_argument('-export_path')
    parser.add_argument('-local_usd_path', type=str)
    parser.add_argument('-local_scene_path')

    parser.add_argument('-f_start', type=int)
    parser.add_argument('-f_end', type=int)


    parser.add_argument('-mode', default='export', choices=['export', 'render'])
    parser.add_argument('-usd_path')
    parser.add_argument('-out_images')
    parser.add_argument('-delegate')
    parser.add_argument('-frame')
    parser.add_argument('-husk_path')

    args = parser.parse_args()


    if args.mode == 'export':
        export_usd(args.scene_path, args.node_path, args.export_path,
                   args.f_start, args.f_end)


    elif args.mode == 'render':
        render_usd_local(args.usd_path, args.out_images,
                         args.delegate, args.frame, args.husk_path)


main()