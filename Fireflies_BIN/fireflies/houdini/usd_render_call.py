import argparse
import os
import sys

import shutil
import time

import hou


def export_usd(scene_path:str, node_path:hou, export_path:str, f_start:int, f_end:int):
    tmp_dir = os.environ.get('TMP')

    norm_scene = os.path.normpath(scene_path)

    norm_dir = os.path.dirname(norm_scene)
    os.startfile(norm_dir)


    # if not os.path.exists(norm_scene):
    #     print("CURRENT PATH: {}".format(scene_path))
    #     print("Scene path is not correct, trying to load again...")
        
    #     time.sleep(350)

    #     print("### Resume ###")

    #     if not os.path.exists(norm_scene):
    #         return
        

    # print("### Copying scene to local dir ###")

    # nas_path = scene_path.replace(os.sep, '/')
    scene_name = os.path.basename(norm_scene)

    # local_scene_path = os.path.join(tmp_dir, scene_name)
    # if os.path.exists(local_scene_path):
    #     os.remove(local_scene_path)

    # try:
    #     shutil.copyfile(norm_scene, local_scene_path)

    # except:
    #     # time.sleep(5)
    #     # shutil.copyfile(scene_path, local_scene_path)

    #     print("### Couldn't copy scene onto local dir ###")
    #     return

    # local_scene_path = local_scene_path.replace(os.sep, '/')

    try:
        hou.hipFile.load(scene_path)

    except:
        time.sleep(60)
        print("### Trying to reload scene ###")
        hou.hipFile.load(scene_path)


    print("### Scene loaded at: {} ###".format(scene_path))

    nas_dir = os.path.dirname(scene_path)
    hou.hscript(f"set -g HIP = '{nas_dir}'")
    hou.hscript(f"set -g JOB = '{nas_dir}'")


    # try:
    #     hou.hipFile.load(scene_path)

    # except:
    #     print("Error while loading scene, reloading...")
    #     time.sleep(120)

    #     print("### Resume ###")

    #     hou.hipFile.load(scene_path)


    target_node = hou.node(node_path)

    stage = target_node.stage()


    export_path = export_path.replace('\\', '/')

    print(export_path)

    for frame in range(f_start, f_end + 1):
        hou.setFrame(frame)
        target_node.cook(force=True)

        stage = target_node.stage()
        out_path = hou.text.expandStringAtFrame(export_path, frame)

        file_name = os.path.basename(out_path)
        tmp_export_path = os.path.join(tmp_dir, file_name).replace(os.sep, '/')

        stage.Export(tmp_export_path)

        out_dir = os.path.dirname(export_path)
        if not os.path.exists(out_dir):
            os.makedirs(out_dir, exist_ok=True)


        try:
            shutil.copyfile(tmp_export_path, out_path)
            os.remove(tmp_export_path)
        
        except:
            print("Error when copying tmp file to final dir -- Exiting")
            return

        

    print("### Fireflies - USD FILES EXPORTED SUCCESSFULLY ###")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-scene_path')
    parser.add_argument('-node_path')
    parser.add_argument('-export_path')

    parser.add_argument('-f_start', type=int)
    parser.add_argument('-f_end', type=int)

    args = parser.parse_args()

    export_usd(args.scene_path, args.node_path, args.export_path, args.f_start, args.f_end)


main()