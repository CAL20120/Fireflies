import os
import sys

import subprocess

import re

from fireflies.context import prod_tracker
CONTEXT = prod_tracker.manage_context()



import maya.cmds as cmds #type:ignore 

from pxr import Usd, UsdUtils, UsdGeom, UsdShade, UsdLux, Sdf


from PySide2 import QtWidgets
from shiboken2 import wrapInstance
import maya.OpenMayaUI as omui #type: ignore


print("Importing -- fireflies maya utils")


def maya_main_window():
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)


#for the future, the purpose would be to set different env vars 
#for the project, shot etc, to let the user use these vars and 
#in the pipeline to easily manage maya paths
def get_mip_path(abs_path:str):
    """
    Get a path relative to the scene root
    """

    print(abs_path)

    mip_path = os.environ.get('MIP')

    if not mip_path:
        print("### Please open a scene with the context tool - MIP path not found ###")
        return

    mip_path = os.path.normpath(mip_path)

    rel_path = os.path.relpath(abs_path, mip_path)

    out_mip = os.path.normpath(rel_path.replace('$MIP', mip_path)).replace('\\', '/')
    out_mip = f"$MIP/{out_mip}"

    print("### MIP generated: {} ###".format(out_mip))

    return out_mip


nspace_to_usdPath = lambda namespace: '/' + namespace.replace(':', '/')


class maya_usd():
    def __init__(self):
        pass


    def import_usd_asset(self, asset_path:str, asset_name:str=None):
        asset_path = get_mip_path(asset_path)

        if not asset_name:
            asset_name = os.path.splitext(os.path.basename(asset_path))[0]
        print(f"### ASSET NAME: {asset_name} ###")


        maya_transform = cmds.createNode("transform", name=asset_name)

        maya_proxyShape = cmds.createNode(
            "mayaUsdProxyShape", parent=maya_transform, name=asset_name
        )

        without_mip = asset_path.strip('$MIP/')

        cmds.setAttr(f"{maya_proxyShape}.filePath", without_mip, type="string")

        cmds.connectAttr("time1.outTime", f"{maya_proxyShape}.time")

        print("### Asset Imported: {} ###".format(asset_name))



    def import_usd_animation(self, animation_path:str, asset_name:str=None):
        anim_dir = os.path.dirname(animation_path)

        anim_master_path = os.path.join(anim_dir, 'master_anim.usd')

        topology_master = os.path.join(anim_dir, 'master_anim.manifest.usd')
        manifest_master = os.path.join(anim_dir, 'master_anim.topology.usd')

        tmp_check_master = [anim_master_path, topology_master, manifest_master]

        check = False
        for path in tmp_check_master: 
            if not os.path.exists(path): 
                check = True
                break

        if check:
            anim_master_path = self.stitch_animation(anim_dir)

        self.import_usd_asset(anim_master_path, asset_name)



    def stitch_animation(self, anim_dir:str) -> str:
        """
        Generates a stitched single usd file from a file sequence \n
        
        Used if the animation is exported in a usd file sequence
        because maya cannot read per frame usd sequences

        Returns:
            out_path: The path of the stitched sequence
        """
        
        # stitch_cmd_path = r"C:\Fireflies\Fireflies_BIN\usd_build_local\scripts\usdstitch.bat"

        anim_pattern = re.compile(r'(.+?)_(\d+)\.usd$')

        target_files = []
        for file in os.listdir(anim_dir):
            file_target = anim_pattern.match(file)

            if file_target:
                target_files.append(
                    f"{os.path.normpath(os.path.join(anim_dir, file))}".replace('\\', '/')
                )

        if not target_files:
            raise FileExistsError("### Could not find the targeted files ###")


        map_files = map(str, target_files)
        str_files = ' '.join(map_files)


        #tried to used directly the .bat usdstitchclips file but because of the 
        #caracter limit in the cmd it's not suitable
        """
        cmd = f"{stitch_cmd_path} --out {out_path} {str_files}"
        # print(cmd)

        proc_env = os.environ.copy()
        proc_env.pop("PYTHONPATH", None)
        proc_env.pop("PYTHONHOME", None)

        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
            text=True, env=proc_env
        )

        stdout, stderr = proc.communicate()
        print(stdout, stderr)
        """

        #getting the rootprim path to pass it as the clipPath
        stage = Usd.Stage.Open(target_files[0])

        default_prim = stage.GetPseudoRoot().GetChildren()
        target_prim = default_prim[0]

        if target_prim.GetName() == "HoudiniLayerInfo":
            target_prim = default_prim[-1]

        clipPath = target_prim.GetPath()

        out_path = os.path.join(anim_dir, 'master_anim.usd')
        topology_master = os.path.join(anim_dir, 'master_anim.manifest.usd')
        manifest_master = os.path.join(anim_dir, 'master_anim.topology.usd')

        tmp_check_master = [out_path, topology_master, manifest_master]

        for path in tmp_check_master:
            if os.path.exists(path):
                os.remove(path)

        out_layer = Sdf.Layer.CreateNew(out_path)

        UsdUtils.StitchClips(
            resultLayer=out_layer, 
            clipLayerFiles=target_files, 
            clipPath=clipPath
        )

        first_file = f"./{os.path.basename(target_files[0])}"
        current_sublayers = list(out_layer.subLayerPaths)

        if first_file not in current_sublayers:
            out_layer.subLayerPaths.append(first_file)

        out_layer.Save()

        print("### Animation master generated ###")

        return out_path





class maya_regular():
    def __init__(self):
        pass


    def reference_maya_scene(self, scene_path:str):
        """
        Method used to reference maya scenes / Import Rigs 
        with the correct namespace relative to the current shot
        """

        work_scene_path = prod_tracker.get_scene_path()

        curr_context = CONTEXT.get_full_ct(work_scene_path)

        if curr_context['is_asset']: 
            raise Exception(
                "### Cannot reference a maya file in an asset creation context ###"
            )
            
        
        curr_entity = curr_context['current_entity']
        shot_name = curr_entity['name']
        sequence_name = curr_entity['sequence_name']

        usd_path = f"/_{sequence_name}_{shot_name}_SHOT/chara"

        new_namespace, asset_name = self.create_namespaces(usd_path)

        scene_path = get_mip_path(scene_path)

        cmds.file(scene_path, reference=True, namespace=new_namespace)



    def create_namespaces(self, nspace_hierarchy:str | list):
        """
        Creates a or multiple namespaces based on a given string 
        or list. If multiple elements are passed, it will create 
        parents based on the order of the elements
        """

        if isinstance(nspace_hierarchy, list): 
            target_parts = nspace_hierarchy

        else:
            if nspace_hierarchy.startswith('/'):
                nspace_hierarchy = nspace_hierarchy.strip('/')

            target_parts = nspace_hierarchy.split('/')


        asset_name = target_parts[-1]

        # target_parts = target_parts[:-1]

        parent = ":"
        for part in target_parts:
            target_name = f"{parent}{part}"
            print(target_name)

            potential_conflits = cmds.ls(part)
            
            if potential_conflits:
                for node in potential_conflits:
                    cmds.rename(node, f"{node}_work")
                    print("### Renamed {} to avoid conflicts with namespaces ###".format(node))

            if not cmds.namespace(exists=target_name):
                t_parent = parent.rstrip(':') if parent != ':' else ':'
                # cmds.namespace(set=parent)
                current_namespace = cmds.namespace(add=part, parent=parent)

                print("### Namespace created {} ###".format(current_namespace))
                
            parent = f"{target_name}:"

        if parent.endswith(':'):
            parent = parent.rstrip(':')

        print(parent)

        return parent, asset_name



    def create_playblast(self, f_range:tuple[float, float], output_path:str) -> str:
        output_path = os.path.normpath(output_path).replace('\\', '/')

        """
        Method to create a maya playblast 

        Args:
            f_range(tuple[int, int]): The targeted frame range, a tuple with \n
            the f_start and f_end values passed as a tuple. 

            output_dir(str):
                The desired output directory
        """

        f_start, f_end = f_range

        if f_start == f_end:
            f_end += 1

        for x in range(int(f_start), int(f_end)):
            cmds.currentTime(x)

            out_path = output_path.replace('####', str(x))

            cmds.playblast(
                completeFilename=out_path,
                format="image",
                compression="jpg",
                quality=100,
                percent=100,
                widthHeight=[2560, 1440],
                viewer=False,
                frame=cmds.currentTime(q=True),
            )




if __name__ == "__main__":
    pass