import argparse 
import os
import shutil 
from datetime import date
import time

import hou


def launch_cache(scene_path:str, node_path:hou, hip_dir:str):
    os.startfile(os.path.dirname(scene_path))    


    hou.hipFile.load(scene_path)
    hou.putenv('HIP', hip_dir)
    
    hou.hscript("varchange")

    target_node = hou.node(f"{node_path}/target_cache")
    print(target_node)

    output_path = target_node.evalParm('sopoutput')

    print("### Output: {} ###".format(output_path))

    output_dir = os.path.dirname(output_path)

    # os.startfile(os.path.normpath(output_dir))

    target_parm = target_node.parm('execute')
    target_parm.pressButton()

    print("### Fireflies - CACHE COMPLETED SUCCESSFULLY ###")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-scene_path')
    parser.add_argument('-node_path')
    parser.add_argument('-render_dir')
    # parser.add_argument('-f_start', type=int)
    # parser.add_argument('-f_end', type=int)

    args = parser.parse_args()

    launch_cache(args.scene_path, args.node_path, args.render_dir)

if __name__ == "__main__":
    main()