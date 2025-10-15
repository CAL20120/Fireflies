#this tool is made for creating quick and automated previz within houdini
import argparse
import threading
from datetime import datetime
import os

import hou

def quick_previz_hou(scene_path):
    print(scene_path)
    images_out = "{}\\images".format(scene_path.rsplit("/", 1)[0])
    
    if not os.path.exists(images_out):
        os.makedirs(images_out)

    scene_path = scene_path.replace("\\", "/")
    print(scene_path)

    task_path = scene_path.rsplit("/", 1)[0]
    output_path = f"{task_path}/previz"

    #we load into the file to launch the previz job
    hou.hipFile.load(file_name=scene_path, ignore_load_warnings=True)

    cur_desktop = hou.ui.curDesktop()
    scene_viewer = hou.paneTabTtype.SceneViewer
    print(scene_viewer.name())
    scene = cur_desktop.paneTabOfType(scene_viewer)

    f_start, f_end = hou.playbar.playbackRange()
    
    scene.flipbookSettings().stash()
    flip_options = scene.flipbookSettings()
    
    flip_options.frameRange((f_start, f_end))
    flip_options.useResolution(True)
    flip_options.useResolution(2560, 1140)

    flip_options.output(f"{images_out}/quick_previz_$F4.jpeg")
    
    scene.flipbook(scene.curViewport(), flip_options)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-scene_path")
    args = parser.parse_args()

    quick_previz_hou(args.scene_path)


main()