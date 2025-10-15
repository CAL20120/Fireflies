import hou 
from pxr import UsdUtils, Sdf, Usd, UsdGeom, Vt, Gf

import subprocess
import random
from datetime import datetime

import os 

print("coucou")

def create_vt_array(primvar_value):
    if primvar_value is None:
        return None
    
    if primvar_value and isinstance(primvar_value, (list, tuple)):
        primv = primvar_value[0]

        if isinstance(primv, float):
            return Vt.FloatArray(primvar_value)
        elif isinstance(primv, int):
            return Vt.IntArray(primvar_value)
        elif isinstance(primv, (list, tuple)) and len(primv) >= 3:
            return Vt.Vec3fArray([Gf.Vec3(*v) for v in primvar_value])
        elif isinstance(primv, (list, tuple)) and len(primv) == 2:
            return Vt.Vec2fArray([Gf.Vec2f(*v) for v in primvar_value])

    return primvar_value

def create_proxy() -> Usd:
    node = hou.pwd()
    stage = node.editableStage()

    for prim in stage.Traverse():
        if prim.GetName() == "render":
            geo_path = prim.GetPath()
            geo_prim = stage.GetPrimAtPath(geo_path)
            geo_children = geo_prim.GetChildren()

            proxy_prim = stage.DefinePrim(f"{geo_path}/proxy", "Scope")

            for children in geo_children:
                if children.GetTypeName() != "Mesh":
                    continue
                new_childen = stage.DefinePrim(f"{proxy_prim.GetPath()}/{children.GetName()}", "Mesh")
                
                result_metadata = []
                for metadata, value in children.GetAllMetadata().items():
                    result_metadata.append(metadata)
                for metadata in result_metadata:
                    if children.HasMetadata(metadata):
                        new_childen.SetMetadata(metadata, children.GetMetadata(metadata))
                
                children_geom = UsdGeom.Mesh(children)
                new_childen_geom = UsdGeom.Mesh(new_childen)

                pts = children_geom.GetPointsAttr().Get()
                counts = children_geom.GetFaceVertexCountsAttr().Get()
                indices = children_geom.GetFaceVertexIndicesAttr().Get()

                if pts and counts and indices:
                    new_childen_geom.GetPointsAttr().Set(Vt.Vec3fArray(pts))
                    new_childen_geom.GetFaceVertexCountsAttr().Set(Vt.IntArray(counts))
                    new_childen_geom.GetFaceVertexIndicesAttr().Set(Vt.IntArray(indices))

                if pts:
                    xs = [p[0] for p in pts]
                    ys = [p[1] for p in pts]
                    zs = [p[2] for p in pts]
                    bbox_min = Gf.Vec3f(min(xs), min(ys), min(zs))
                    bbox_max = Gf.Vec3f(max(xs), max(ys), max(zs))

                children_privars = UsdGeom.PrimvarsAPI(children)
                new_childen_primvars = UsdGeom.PrimvarsAPI(new_childen)

                for primvar in children_privars.GetPrimvars():
                    var_name = primvar.GetBaseName()
                    var_type = primvar.GetTypeName()
                    var_value = primvar.Get()
                    var_interpolation = primvar.GetInterpolation()

                    new_primvars = new_childen_primvars.CreatePrimvar(var_name, var_type, var_interpolation)
                    value = create_vt_array(var_value)
                    if value is not None:
                        new_primvars.Set(value)

                    indices_test = primvar.GetIndicesAttr().Get()
                    if indices_test:
                        new_primvars.SetIndices(Vt.IntArray(indices_test))
                children_geom.GetPurposeAttr().Set("render")
                new_childen_geom.GetPurposeAttr().Set("proxy")
                new_childen.SetActive(True)





class fireflies_layout():
    def __init__(self):
        self.hython_path = r"C:\Fireflies\Common\Houdini_vars\houdini_205445\Houdini20.5.445\bin\hython.exe"
        self.backup_path = hou.hipFile.path()
        self.scene_path = hou.hipFile.path().rsplit("/", 1)[0]
        self.scene_name = self.scene_path.rsplit("/")[-1]

    def quick_previz(self) -> hou:
        print("creating previz")
        current_date = datetime.now()
        export_date = f"{current_date.hour}_{current_date.minute}_{current_date.day}_{current_date.month}_{current_date.year}"
        export_path = f"{self.scene_path}/quick_preview/preview_{self.scene_name}/{export_date}"
    
        if not os.path.exists(export_path):
            os.makedirs(export_path)

        #tmp export
        #we need to save either a regular hip of nc
        export_name = f"{export_path}/{self.scene_name}_quick_previz.hipnc"
        hou.hipFile.save(file_name=export_name)
        
        #we load back into the original scene to let the script run in background
        #and let the artist work on their scene
        hou.hipFile.load(file_name=self.backup_path, ignore_load_warnings=True)
        
        
        #we want to launch a background hython job
        subprocess.run(
            '"C:\\Fireflies\\Common\\Houdini_vars\\houdini_205445\\Houdini20.5.445\\bin\\hython.exe" "C:\\Fireflies\\Fireflies_BIN\\fireflies\\fireflies_utils\\usd\\\quick_previz.py" -asset_path {}'.format(export_name), 
            shell=True, stdout=subprocess.PIPE
        )


class publish_layout():
    def __init__(self):
        self.scene_path = hou.hipFile.path().rsplit("/", 1)[0]
        self.export_path = f"{self.scene_path}/usd_published"
        self.scene_name = self.scene_path.rsplit("/")[-1]

    def publish_layout(self):
        #we need  to find the current top of the hda.
        if not os.path.exists(self.export_path):
            os.makedirs(self.export_path)
        
        current_node = hou.pwd()
        # print(kwargs)
        current_path = current_node.path()

        target_rop = "{}/publish_layout".format(current_path)
        node_export = hou.node(target_rop)

        custom_name = current_node.evalParm('custom_input')

        if custom_name != "":
            target_export = f"{self.export_path}/{self.scene_name}_{custom_name}_layout.usd"
        else:
            target_export = f"{self.export_path}/{self.scene_name}_layout.usd"

        node_export.parm('lopoutput').set(target_export)
        
        node_export.parm('trange').set(1)

        target = None
        if True:
            node_export.parm('execute').pressButton()

