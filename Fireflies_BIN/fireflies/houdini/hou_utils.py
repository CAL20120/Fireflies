#This file contains all the classes and methods often used when interacting with houdini hou module in usd
import hou

import os
from datetime import datetime
import subprocess
import re

print("Importing -- hou_utils.py")

class hou_usd():
    def __init__(self):
        self.scene_path = hou.hipFile.path().rsplit("/", 1)[0]
        self.scene_name = self.scene_path.rsplit("/")[-1]
        self.prod_name = hou.hipFile.path().rsplit("/")[-5]
        self.prod_path = hou.hipFile.path().rsplit("/", 4)[0].replace("/", "\\")
        self.curr_context = self.get_current_context()

    def return_paths(self) -> str:
        return self.prod_path
    

    def get_current_context(self) -> hou:
        try:
            desktop = hou.ui.curDesktop()
        
        except:
            print("Couldn't find the hou ui")
            desktop = None
            return


        self.pane = desktop.paneTabOfType(hou.paneTabType.NetworkEditor)
        self.curr_context = self.pane.pwd()

        # curr_path = curr_context.path()

        return self.curr_context


    def center_node(self, current_node:hou):
        self.get_current_context()

        bound = self.pane.visibleBounds()
        target_cor = bound.center()
        
        current_node.setPosition(target_cor)


    def import_prod_usd_asset(self, asset_path):
        asset_name = asset_path.rsplit("/", 1)[-1].split(".", 1)[0]

        #we need to get the current context path to create the node that will reference our 
        #target asset
        desktop = hou.ui.curDesktop()
        pane = desktop.paneTabOfType(hou.paneTabType.NetworkEditor)
        curr_context = pane.pwd()


        if curr_context.type().name() == 'lopnet':
            asset_node = curr_context.createNode("assetreference", asset_name)

        else: 
            asset_node = curr_context.createNode("usdimport", asset_name)
            unpack_node = curr_context.createNode("unpackusd", "unpack_usd")

            unpack_node.setInput(0, asset_node)

            asset_node.parm('purpose').set('render')

            unpack_node.parm('transferattributes').set('*')
            unpack_node.parm('importprimvars').set('*')
            unpack_node.parm('importattributes').set('*')


        try:
            asset_node.parm('filepath').set(asset_path)
    
        except:
            asset_node.parm('filepath1').set(asset_path)
            unpack_node.parm('output').set(1)
            self.center_node(unpack_node)

        self.center_node(asset_node)



    def import_usd_sequence(self, asset_path):
        curr_context = self.get_current_context()
        asset_name = asset_path.rsplit("/", 1)[-1].split(".", 1)[0]

        target_path = re.search(r'(.+?)_(\d+)\.usd$', asset_path)

        if not target_path:
            print("no sequence file detected")
            return
        
        udim_num = str(target_path.group(2))
        path = target_path.group().replace(udim_num, '$F4')

        if curr_context.type().name() == 'lopnet':
            sublayer_node = curr_context.createNode("sublayer", asset_name.rsplit('_', 1)[0])
            sublayer_node.parm('filepath1').set(path)

            self.center_node(sublayer_node)


    def import_regular_asset(self, asset_path:str):
        # asset_name = os.path.basename(asset_path)

        if self.curr_context.type().name() == "lopnet":
            asset_node = self.curr_context.createNode('Fireflies::regular_asset_import')
            asset_node.parm('input_file').set(asset_path)

            self.center_node(asset_node)

        if self.curr_context.type().name() == "sopnet":
            file_node = self.curr_context.createNode('file')
            file_node.parm('file').set(asset_path)

            self.center_node(file_node)


    def import_light(self, asset_path, asset_name):
        curr_context = self.get_current_context()
        
        light_node = curr_context.createNode("domelight::3.0", asset_name)
        light_hou = hou.node(light_node.path())

        correct_path = asset_path.replace('\\', '/')
        light_hou.parm('xn__inputstexturefile_r3ah').set(correct_path)

        light_hou.setColor(hou.Color(0.3, 0, 0.5))
    
        self.center_node(light_node)


    def build_render_path(self, version):
        
        export_dir = f"{self.scene_path}/render_{self.prod_name}/{self.prod_name}_{version}"
        export_path = f"{export_dir}/{self.prod_name}_{version}_render_$F4.exr"

        if not os.path.exists(export_dir):
            os.makedirs(export_dir)

        return export_path


    def filter_render_prims(self):
        from pxr import Usd, Sdf

        node = hou.pwd()
        stage = node.editableStage()

        prim = None

        target_paths = []
        for prim in stage.Traverse():
            if not "render" in str(prim.GetPath()):
                target_paths.append(prim.GetPath())

        for path in target_paths:
            stage.RemovePrim(path)
        
        # stage.GetRootLayer().save()

    def create_proxy_purpose(self):
        from pxr import Usd, UsdGeom

        node = hou.pwd()
        stage = node.editableStage()

        for prim in stage.Traverse():
            if prim.GetTypeName() == "Mesh":
                target_geom = UsdGeom.Mesh(prim)
                target_geom.GetPurposeAttr().Set('proxy')


    def show_preview(self, asset_path):
        print("opening {}".format(asset_path))
        asset_path.replace("/", "\\")
        
        # "C:\\Fireflies\\Common\\usd_viewer\\usdview_win32\\scripts\\usdview_gui.bat {}".format(asset_path)
        usdview_path = r"C:\Fireflies\Common\usd_viewer\usdview_win32\scripts\usdview_gui.bat"
        
        env = os.environ.copy()
        if os.path.exists(asset_path):
            subprocess.Popen(
                [
                    usdview_path,
                    asset_path
                ],
                env=env, creationflags=subprocess.CREATE_NEW_CONSOLE, cwd=os.path.dirname(usdview_path), shell=True
            )

        else: 
            print("asset path does not exist")


    def create_playblast(self, output:str):
        desktop = hou.ui.curDesktop()
        target_pane = desktop.paneTabOfType(hou.paneTabType.SceneViewer)

        viewport = target_pane.curViewport()

        # output = f"{self.scene_path}/quick_preview/{0}/{self.scene_name}.png"
        # f_start, f_end = hou.playbar.playbackRange()

        fbk_settings = target_pane.flipbookSettings().stash()
        fbk_settings.frameRange((hou.frame(), hou.frame()))
        fbk_settings.useResolution(True)
        fbk_settings.useResolution((1920, 1080))
        
        fbk_settings.outputToMPlay(False)
        fbk_settings.output(output)

        target_pane.flipbook(viewport, fbk_settings)

        print("preview exporter to: {}".format(output))


    def path_converter(self, path:str) -> str:
        os.path.normpath(path)

        HIP = os.environ.get('HIP')
        os.path.normpath(HIP)

        relative_path = os.path.relpath(path, HIP)

        norm_rel = relative_path.replace('\\', '/')
        hip_path = f"$HIP/{norm_rel}"

        return hip_path


from pxr import Usd, UsdGeom, UsdSkel, Sdf, UsdUtils
class usd_utils():
    def __init__(self):
        pass

    def rig_test(self, node:hou):
        stage = node.Stage()

        target_skel = [prim for prim in stage.Traverse() if prim.IsA(UsdSkel.Skeleton)]
        # print(target_skel)

        target_geo_path = None

        binding = UsdSkel.BindingAPI.Apply(target_prim=None)
        binding.CreateAnimationSourceRel().SetTargets(
            [target_geo_path]
        )


        skelCache = UsdSkel.Cache()

        for prim in target_skel:
            if prim.IsA(UsdSkel.Skeleton):
                target_skel.PruneChildren()

                skelCache.Populate(prim, Usd.TraverseInstanceProxies())

                bindings = skelCache.ComputeSkelBindings(
                    prim, Usd.TraverseInstanceProxies()
                )

                for binding in bindings: 
                    skelQuery = skelCache.GetSkelQuery(binding.GetSkeleton())

                    skinningXform = skelQuery.ComputeSkinningTransforms(time=None)
                    if not skinningXform:
                        return
                    
                    for skinningQuery in binding.GetSkinningTargets():
                        primSkinning = skinningQuery.GetPrim()




if __name__ == "__main__":
    pass

