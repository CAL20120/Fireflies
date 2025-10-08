import hou 
from pxr import UsdUtils, Sdf, Usd, UsdGeom, Vt, Gf

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

def create_proxy():
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

def publish_layout():
    pass
