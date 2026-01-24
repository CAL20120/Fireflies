#This file contains all the classes and methods often used when interacting with houdini hou module in usd
import hou

import os
from datetime import datetime
import subprocess
import re

print("Importing -- hou_utils.py")
from pxr import Usd, UsdGeom, UsdSkel, Sdf, UsdUtils, UsdShade, UsdRender

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


    def get_last_node(self, scene_path:str) -> hou.node:
        pass



    def quick_wind(self, prim_path:str):
        node = hou.pwd()
        node_path = node.path()

        stage_ref = hou.node(f"{node_path}/stage_ref")

        print(prim_path)

        stage = stage_ref.stage()

        asset_prim = stage.GetPrimAtPath(prim_path)
  
        target = f"{prim_path}/GEO/render"
        target_prim = stage.GetPrimAtPath(target)
        iter_prims = iter(Usd.PrimRange(target_prim))

        for prim in iter_prims:
            mesh = UsdGeom.Mesh(prim)
            if mesh:
                mesh_prim = prim

        if not mesh_prim:
            print("No mesh was found")
            return
            
        # bind = UsdShade.MaterialBindingAPI(mesh_prim)
        # bind_mat = bind.GetDirectBinding()

        mat_prim, rel = UsdShade.MaterialBindingAPI(mesh_prim).ComputeBoundMaterial()

        print(mat_prim)

        mat_prim_path = mat_prim.GetPath()

        test = str(mat_prim_path)

        target_mat_node = hou.node(f"{node_path}/target_mat")
        target_mat_node.parm('matpath1').set(test)
        load_btn = target_mat_node.parm('load1')
        load_btn.pressButton()


        check_displace = False
        for child in mat_prim.GetPrim().GetChildren():
            shader = UsdShade.Shader(child)

            if shader:
                target_id = shader.GetIdAttr().Get()

                if target_id == "PxrDisplace":
                    print("First displace found")
                    check_displace = True


        collect_node = target_mat_node.node('collect1')
        collect_inputs = collect_node.inputs()

        quick_wind_node = target_mat_node.createNode('wind_setup_disp', 'wind_disp')
        wind_node_output = quick_wind_node.outputNames()

        quick_wind_node.allowEditingOfContents()


        if check_displace:
            print("Connecting wind displace to current")

            for x, node in enumerate(collect_inputs):
                if node.type().name() == "pxrdisplace::3.0":
                    disp_node = node


            if not disp_node:
                print("Error when finding the current disp node")
                return

            # collect_disp = collect_node.inputIndex('displace_out')
            # disp_node = collect_node.input(collect_disp)

            in_disp_node = disp_node.inputIndex('dispScalar')
            old_node = disp_node.input(in_disp_node)
            old_node_outputs = old_node.outputNames()
            resultF_old = old_node_outputs.index('resultF')


            disp_mix_node = target_mat_node.createNode('pxrdispscalarlayer', 'disp_mix')
            disp_mix_inputs = disp_mix_node.inputNames()
            disp_mix_outputs = disp_mix_node.outputNames()            

            base_layer = disp_mix_inputs.index('baseLayerDispScalar')
            disp_mix_node.setInput(base_layer, old_node, resultF_old)

            resultR_wind = wind_node_output.index('resultR')

            wind_layer = disp_mix_inputs.index('layer1DispScalar')
            disp_mix_node.setInput(wind_layer, quick_wind_node, resultR_wind)

            layer_out = disp_mix_outputs.index('resultF')
            disp_node_inputs = disp_node.inputNames()
            target_input = disp_node_inputs.index('dispScalar')

            disp_node.setInput(target_input, disp_mix_node, layer_out)


        else: 
            wind_disp_out = wind_node_output.index('displace_out')

            target_input_collect = len(collect_inputs)
            collect_node.setInput(target_input_collect, quick_wind_node, wind_disp_out)



    def create_light_group_var(self):
        #this method is used in the fireflies rm render node as a callback
        
        current_node = hou.pwd()
        stage = current_node.editableStage()

        node = current_node.parent()

        # print(stage)

        node_ancestors = node.inputAncestors()

        grp_name = node.evalParm('grp_name')

        if not grp_name:
            return
        
        print(grp_name)

        for ancestor in node_ancestors:
            if "light" in ancestor.type().name():
                print(ancestor)

                group_create = ancestor.parm('xn__inputsrilightlightGroup_control_krbcf')
                group_input = ancestor.parm('xn__inputsrilightlightGroup_jebcf')

                if not group_input:
                    continue

                group_create.set('set')
                group_input.set(grp_name)

        
        grp_var_path = f"/Render/Products/Vars/light_grp_{grp_name}"
        
        target_var = UsdRender.Var.Define(stage, grp_var_path)
        
        target_var.CreateSourceNameAttr().Set(f"C[DS]*<L.'{grp_name}'>")
        target_var.CreateSourceTypeAttr().Set(UsdRender.Tokens.lpe)

        target_var.GetPrim().CreateAttribute('driver:parameters:aov:name', Sdf.ValueTypeNames.String).Set(grp_name)
        target_var.CreateDataTypeAttr().Set("color3f")

        print("VAR CRTEATED: {}".format(grp_name))





if __name__ == "__main__":
    pass
