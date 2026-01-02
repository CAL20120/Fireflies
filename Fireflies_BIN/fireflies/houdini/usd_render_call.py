import argparse
import os
import sys

import hou


def export_usd(scene_path:str, node_path:hou, export_path:str, f_start:int, f_end:int):
    if not os.path.exists(scene_path):
        print("Scene path is not correct")
        return

    hou.hipFile.load(scene_path)
    
    target_node = hou.node(node_path)

    stage = target_node.stage()


    export_path = export_path.replace('\\', '/')

    print(export_path)

    for frame in range(f_start, f_end + 1):
        hou.setFrame(frame)
        target_node.cook(force=True)

        stage = target_node.stage()
        out_path = hou.text.expandStringAtFrame(export_path, frame)

        stage.Export(out_path)

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