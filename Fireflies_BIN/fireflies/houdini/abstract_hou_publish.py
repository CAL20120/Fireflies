import os
import sys

import re
import random

import subprocess

import json

from fireflies.houdini import hou_utils

from fireflies.context import prod_tracker
CONTEXT = prod_tracker.manage_context()

try:
    import hou

except:
    pass

from pxr import Usd, UsdGeom, Sdf, UsdUtils, UsdShade


class hou_publish():
    def __init__(self):
        super(hou_publish, self).__init__()


        self.utils = hou_utils.hou_usd()
        self.curr_context = self.utils.get_current_context()
        
        try:
            self.scene_path = os.path.dirname(hou.hipFile.path())
            self.export_dir = f"{self.scene_path}/usd_published/"

        except:
            pass



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

                if root_prim.GetName() == "HoudiniLayerInfo":
                    continue

                target_prim = root_prim.GetChildren()[0]

                if target_prim.GetName() == "HoudiniLayerInfo":
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

        return target_name, target_paths, target_prims, target_nodes, 
        

    def get_last_version(self, asset_name:str, target_export_dir:str=None):
        version_id = 1
        version_check = True
    
        if target_export_dir:
            self.export_dir = target_export_dir


        while version_check:
            export_dir = f"{self.export_dir}/{asset_name}/{asset_name}_{version_id:03}"
            
            exists = os.path.exists(export_dir)
            if not exists:
                os.makedirs(export_dir)
                break
            version_id += 1

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


        """
        stage = Usd.Stage.CreateNew(export_path)
        
        UsdUtils.CopyLayerMetadata(
            source=None,
            destination=stage.GetRootLayer(),
            skipSubLayers=False
            
        )

        """

        # we want to only export the current layer (what's after a layer break in houdini in this case)
        # because when exporting a task otherwise we would get the whole stage instead of the targeted layer
        # stack
        current_layer = root_prim.GetPrimStack()[0].layer


        # self.resolve_relative_paths(stage = target_stage, export_path=export_path, target_layer=current_layer)

        target_stage.SetEditTarget(current_layer)

        target_stage.Save()

        current_layer.Export(export_path)

        # self.resolve_relative_paths(stage_path=export_path)

        return export_path


    #we use this method to export assemblies, because exporting a single layer
    #results in an empty usd file
    def export_full_stack(self, asset_name:str, current_node):
        if not os.path.exists(self.export_dir):
            os.makedirs(self.export_dir)

        export_dir, export_path = self.get_last_version(asset_name=asset_name)
        print(export_path)

        stage = current_node.stage()
        root_layer = stage.GetRootLayer()

        # export_path = f"{export_path.rsplit('.', 1)[0]}.usda"

        # target_sublayers = stage.GetRootLayer().subLayerPaths
        # # out_stage = Usd.Stage.CreateNew(export_path)

        # for layer in target_sublayers:
        #     out_stage.GetRootLayer().subLayerPaths.append(layer)


        target_layers = []

        for path in root_layer.subLayerPaths:
            if "anon" in path:
                continue

            target_layers.append(str(path).strip('@'))


        out_sublayers = []
        for path in target_layers:
            relative_path = os.path.relpath(path, export_dir)
            out_relative = relative_path.replace("\\", "/")

            out_sublayers.append(out_relative)

        root_layer.subLayerPaths = out_sublayers

        root_layer.Export(export_path)

        stage.Save()



    def extract_animation(self, root_prim:Usd, node):
        if not os.path.exists(self.export_dir):
            os.makedirs(self.export_dir)

        f_start, f_end = hou.playbar.playbackRange()
        
        asset_name = str(root_prim.GetName())

        export_dir, _ = self.get_last_version(asset_name=asset_name)

        # export_path = "{}/{}.usd".format(self.export_dir, asset_name:04d)

        for frame in range(int(f_start), int(f_end) + 1):
            hou.setFrame(frame)
            stage = node.stage()

            export_path = f"{export_dir}/{asset_name}_{frame}.usd"
            # print(export_path)
            stage.Export(export_path)


    def debug_export(self, root_prim:Usd, node):
        if not os.path.exists(self.export_dir):
            os.makedirs(self.export_dir)

        asset_name = str(root_prim.GetName())

        _, export_path = self.get_last_version(asset_name=asset_name)

        stage = node.stage()

        stage.Export(export_path)

        return export_path




    def get_export_path(self, asset_name):
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

        return export_dir, target_version



    def write_commentary(self, text, asset_name):
        export_dir, target_version = self.get_export_path(asset_name)

        comment_dir = "{}/metadata/commentary".format(target_version)
        comment_dir = os.path.join(export_dir, comment_dir)

        comment_path = f"{comment_dir}/{asset_name}_comment.txt"

        print(comment_path)

        if not os.path.exists(comment_dir):
            os.makedirs(comment_dir)

        with open(comment_path, "w") as f:
            f.write(text)



    def export_preview(self, asset_name) -> str:
        export_dir, target_version = self.get_export_path(asset_name)

        preview_dir = "{}/metadata/preview".format(target_version)

        preview_dir = os.path.join(export_dir, preview_dir)
        preview_path = f"{preview_dir}/{asset_name}_preview.jpg"

        if not os.path.exists(preview_dir):
            os.makedirs(preview_dir)

        self.utils.create_playblast(output=preview_path)
        
        print("### PREVIEW: {} ###".format(preview_path))
        
        return preview_path


    def export_video_preview(self, asset_name, scene_path=None):
        export_dir, target_version = self.get_export_path(asset_name)

        preview_dir = "{}/metadata/video_preview".format(target_version)
        out_dir = os.path.join(export_dir, preview_dir)

        preview_path = f"{out_dir}/{asset_name}_preview_$F4.jpg"

        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

        if prod_tracker.CT_HOU:
            f_start, f_end = hou.playbar.playbackRange()
            frame_range = (int(f_start), int(f_end))

            self.utils.create_playblast(preview_path, frame_range)

        print("### Playblast Done ###")

        kt_infos = None
        if scene_path:
            kt_infos = CONTEXT.get_full_ct(scene_path)
            print("### Fetched kt infos for preview ###")

            #we need to convert the dict to pass it to argparse
            kt_infos_json = json.dumps(kt_infos)
            kt_infos_json = kt_infos_json.replace('""', '\\"')

            kt_infos = kt_infos_json

            print("### KT INFO converted to json schema ###")

            kt_user = CONTEXT.kt_user['full_name']

        first_frame = preview_path.replace('$F4', str(frame_range[0]))
        print(first_frame)

        local_appdata = os.environ.get('LOCALAPPDATA')

        script_path = "C:\\Fireflies\\Fireflies_BIN\\fireflies\\fireflies_utils\\video_converter.py"
        python_path = f"{local_appdata}\\Programs\\Python\\Python310\\python.exe"

        #otherwise houdini with launch the process with hython
        proc_env = os.environ.copy()
        proc_env.pop("PYTHONPATH", None)
        proc_env.pop("PYTHONHOME", None)

        proc_cmd = [
            python_path, script_path, '-first_image_path', first_frame, '-kt_infos', kt_infos, '-user', kt_user
        ]

        proc = subprocess.Popen(
            proc_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=proc_env
        )

        stdout, stderr = proc.communicate()

        print(stdout)
        print("##############")
        print(stderr)


        print("### Preview video generated ###")

        out_video_path = os.path.join(preview_dir.replace('/', '\\'), 'video_preview.mkv')
        preview_full_path = os.path.join(export_dir.replace('/', '\\'), out_video_path)
        
        print("### out video: {} ###".format(preview_full_path))

        if not os.path.exists(preview_full_path):
            raise FileExistsError("### Couldn't find the video preview -- Exiting ###")

        return preview_full_path
        
    


class Publish_checks():
    def __init__(self):
        super(Publish_checks, self).__init__()
        pass


    def resolve_relative_paths(self, stage_path:Usd) -> Usd.Stage:
        if not stage_path:
            print("No stage found")
            return

        print("### CORRECTING PATHS ###")

        # print(stage_path)
        # tmp_export_dir = "tmp_export/tmp_check_{}.usd".format(
        #     random.randrange(0000, 9999)
        # )
        
        # test = os.path.dirname(stage_path)
        # tmp_export_path = f"{test}/{tmp_export_dir}".replace(os.sep, '/')
        
        # x = os.path.dirname(tmp_export_path)
        # if not os.path.exists(x):
        #     os.makedirs(x)

        # current_stage = current_stage.stage()

        # current_stage.GetRootLayer().Export(tmp_export_path)
        
        
        rel_dir = os.path.dirname(stage_path)


        stage = Usd.Stage.Open(stage_path)

        print("########## STAGE #########")
        # stage = hou_node.stage()

        print(stage)

        # stage.SetEditTarget(stage.GetRootLayer())


        for prim in stage.Traverse():
            if prim.GetName() == "HoudiniLayerInfo":
                continue

            print(prim)

    
        for prim in stage.TraverseAll():
            if prim.GetName() == "HoudiniLayerInfo":
                continue

            shader = UsdShade.Shader(prim)
            if not shader:
                print("Not Shader")
                continue


            for input in shader.GetInputs():
                input_name = input.GetBaseName()
                print("input: {}".format(input_name))

                if "filename" in input_name.lower():
                    tex_path = input.Get()
                    print(tex_path)

                    # if not tex_path:
                    #     continue
                
                    tex_path = str(tex_path).strip('@')

                    if not os.path.isabs(tex_path):
                        print("Path is already relative")
                        continue


                    if tex_path.startswith('$HIP'):
                        tex_path = hou.text.expandString(tex_path)

                    # if os.path.isabs(tex_path):
                    print("##########################")
                    print(tex_path)
                    print(rel_dir)
                    print("##########################")
                    rel_path = os.path.relpath(tex_path, rel_dir).replace(os.sep, '/')

                    print(rel_path)

                    print(os.path.abspath(rel_path))
                    
                    input.Set(Sdf.AssetPath(rel_path))


        # target_layer.Save()
        # target_layer.Export(export_path)

        stage.GetRootLayer().Export(stage_path)




    def check_asset_structure(self, node_path:Usd):
        tmp_dir = os.path.join(os.environ.get('HIP'), 'tmp_checks')

        if not os.path.exists(tmp_dir):
            os.makedirs(tmp_dir)


        tmp_id = random.randint(1111, 9999)

        tmp_export_path = os.path.join(tmp_dir, f"asset_check_{tmp_id}.usda").replace('\\', '/')
        print(tmp_export_path)


        current_node = hou.node(node_path)
        stage = current_node.stage()

        stage.Export(tmp_export_path)

        stage = Usd.Stage.Open(tmp_export_path)

        asset_prim = stage.GetPseudoRoot().GetChildren()

        asset_name = asset_prim[-1].GetName()
        if asset_name == "HoudiniLayerInfo":
            asset_name = asset_prim[0].GetName()

        if not "_ASSET" in asset_name.upper():
            print("### Inconnrect asset name ###")
            return False

        # check_list = []
        # for prim in stage.Traverse():
        #     if any(
        #         name in target_prims for name in str(prim.GetName()).lower()):
        #         check_list.append(prim.GetName())

        #         if prim.GetTypeName() != "Xform":
        #             print("Wrong prim type -- Exiting")
        #             return

        target_paths = [
            f"/{asset_name}/GEO",
            f"/{asset_name}/mtl"
        ]

        print(target_paths)

    
        check_len = False
        for path in target_paths:
            try:
                prim = stage.GetPrimAtPath(path)

                if not prim.GetTypeName() == "Xform":
                    print("### Wrong prim type for {} ###".format(prim.GetName()))
                    return False

                check_len = True

                print("Match")
            
            except:
                print(
                    "### Couldn't find prim at: {} -- Exiting ###".format(path)
                )


        target_geo_paths = [
            f"/{asset_name}/GEO/proxy",
            f"/{asset_name}/GEO/render",
        ]


        for path in target_geo_paths:
            try: 
                prim = stage.GetPrimAtPath(path)
                
                if prim.GetTypeName() != "Scope":
                    print("### Wrong GEO scope type ###")
                    return False

            except:
                return False


        exclude_render_types = ["Xform", "Scope"]

        render_scope = stage.GetPrimAtPath(target_geo_paths[-1])
        for child in render_scope.GetChildren():
            child_type = child.GetTypeName()

            if any(ext in exclude_render_types for ext in child_type):
                print("### Detected wrong prims in the render scope ###")
                return False



        if not check_len:
            print("### Mismatch with prims -- Exiting ###")
            return False
        

        os.remove(tmp_export_path)


if __name__ == "__main__":
    print("Using publish hou utils")