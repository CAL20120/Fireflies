import os
import sys
import re

from fireflies.houdini import hou_utils

import hou

from pxr import Usd, UsdGeom, Sdf, UsdUtils


class hou_publish():
    def __init__(self):
        super(hou_publish, self).__init__()

        self.utils = hou_utils.hou_usd()
        self.curr_context = self.utils.get_current_context()
        self.scene_path = os.path.dirname(hou.hipFile.path())

        self.export_dir = f"{self.scene_path}/usd_published/"

    def fetch_targets(self):
        #in houdini, we have a special parameter "publish" on nulls that defines wich are the targeted publishable assets

        print(self.curr_context)

        target_name = []
        target_paths = []
        target_prims = []
        target_nodes = []

        for node in self.curr_context.allSubChildren():
            target_parm = node.parm('target_publish')
            if target_parm:
                stage = node.stage()
                if not stage:
                    print("No stage found")
                    return

                #in solaris GetDefaultPrim returns an invalid prim
                root_prim = stage.GetPseudoRoot()
                if not root_prim:
                    continue

                target_prim = root_prim.GetChildren()[-1]

                prim_name = target_prim.GetName()
                prim_path = str(target_prim.GetPath())

                target_name.append(prim_name)
                target_paths.append(prim_path)
                target_prims.append(target_prim)

                target_nodes.append(node)

        # print(zip(target_prim, target_paths))

        print(target_name)
        print(target_paths)

        return target_name, target_paths, target_prims, target_nodes 
        

    def get_last_version(self, asset_name:str):
        version_id = 1
        version_check = True
    
        while version_check:
            export_dir = f"{self.export_dir}/{asset_name}/{asset_name}_{version_id:03}"
            exists = os.path.exists(export_dir)
            # export_path = f"{export_dir}/{asset_name}.usd"

            if not exists:
                os.makedirs(export_dir)
                break
            version_id += 1

            # else:
            #     if exists:
            #         version_id += 1
            #     else: 
            #         version_id -=1
            #         break

        # export_dir = f"{self.export_dir}/{asset_name}/{asset_name}_{version_id:03}"
                
        export_path = f"{export_dir}/{asset_name}.usd"


        return export_dir, export_path


    def extract_usd(self, root_prim:Usd):
        if not os.path.exists(self.export_dir):
            os.makedirs(self.export_dir)

        # stage = node.stage()

        # asset_name = node.evalParm('asset_name')
        # export_path = "{}/{}.usd".format(self.export_dir, asset_name)

        asset_name = str(root_prim.GetName())

        target_stage = root_prim.GetStage()

        _, export_path = self.get_last_version(asset_name=asset_name)
        print(export_path)

        # stage = Usd.Stage.CreateNew(export_path)
        
        # UsdUtils.CopyLayerMetadata(
        #     source=None,
        #     destination=stage.GetRootLayer(),
        #     skipSubLayers=False
            
        # )

        target_stage.Export(export_path)



    def extract_animation(self, root_prim:Usd, node:hou):
        f_start, f_end = hou.playbar.playbackRange()
        
        asset_name = str(root_prim.GetName())

        export_dir, _ = self.get_last_version(asset_name=asset_name)

        # export_path = "{}/{}.usd".format(self.export_dir, asset_name:04d)


        if not os.path.exists(self.export_dir):
            os.makedirs(self.export_dir)

        for frame in range(int(f_start), int(f_end)):
            hou.setFrame(frame)
            stage = node.stage()

            export_path = f"{export_dir}/{asset_name}_{frame}.usd"
            stage.Export(export_path)


    def write_commentary(self, text, asset_name):
        export_dir = f"{self.export_dir}/{asset_name}"

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

        comment_dir = "{}/metadata/commentary".format(target_version)
        # comment_dir = os.path.join(export_dir, comment_dir)
        comment_dir = f"{export_dir}/{comment_dir}"
        comment_path = f"{comment_dir}/{asset_name}_comment.txt"

        print(comment_path)

        if not os.path.exists(comment_dir):
            os.makedirs(comment_dir)

        with open(comment_path, "w") as f:
            f.write(text)


    def export_preview(self):
        pass