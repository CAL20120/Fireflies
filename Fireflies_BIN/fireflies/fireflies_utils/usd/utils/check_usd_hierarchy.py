import os
import maya.cmds as cmds 
import maya.mel as mel 

from pxr import Usd, Sdf, UsdGeom
import pyblish.api

class usd_check_hierarchy():

    def __init__(self):
        super(usd_check_hierarchy, self).__init__()


    def export_usd_check(self, asset_name) -> Usd: 
        # self.instance = pyblish.api.Context()
        # self.context = self.instance.context
        # asset_name = self.instance.append("asset_name")
        # print(asset_name)

        self.shot_path = cmds.file(q=True, sn=True).rsplit("/", 2)[0]
        self.export_path = f"{self.shot_path}/tmp_check/{asset_name}.usda"
        self.final_sel = cmds.listRelatives(asset_name, fullPath=True)
        # selection = cmds.select(asset_name) 
        # asset_name = asset_name

        # temp = tempfile.NamedTemporaryFile(prefix = "USD", suffix = ".usd")
        # print(f"\n {temp.name} \n")
        # print(temp)
    
        #when temp is called, it writes the file, yet the file stays open while we don't tell temp to close it
        #if we don't do so, maya can't edit it and add the usd data to it
        # temp.close()
        cmds.select(cmds.listRelatives(asset_name))

        # we use the officiel export function instead of an export to string because it is easier
        # to export a selection like so. Then we can export the stage to string to apply modifications
        cmds.mayaUSDExport(
            file = self.export_path,
            selection = True,
        )

        # A ne surtout pas faire, sinon on supprime effectivement le proxy, mais les données usd restent en mémoire dans maya
        # et deviennent inaccessibles.
        "cmds.delete(proxyShapeTest)"

        # temp.close()
        # temp.delete(True)
        print("\n Usd file exported to %s! \n" % self.export_path)

        stage = Usd.Stage.Open(self.export_path)
        root_path = Sdf.Path(f"/{asset_name}")


        #maya automatically writes a "mtl" scope with a shader parented to the geo, we want to clean that 
        mtl_init_path = Sdf.Path(f"/{asset_name}/mtl")
        print(f"{mtl_init_path}")
        mtl_init_prim = stage.GetPrimAtPath(mtl_init_path)
        mtl_children = mtl_init_prim.GetChildren()
        for children in mtl_children:
            print(type(children))
            stage.RemovePrim(children.GetPath())

        #debug export
        stage.GetRootLayer().Save()
        output = str(stage.GetRootLayer().ExportToString())
        with open(f"{self.shot_path}/tmp/test_edit.usda", "w") as f:
            f.write(output)


        #change prim types to get the correct hierarchy
        root_prim = stage.GetPrimAtPath(root_path)
        iter_prims = iter(Usd.PrimRange(root_prim))
    
        # mtl_prim = stage.DefinePrim(f"/{asset_name}/test", "mtl")
        # mtl_prim.SetSpecifier(Sdf.SpecifierOver)
        # mtl_prim.SetTypeName("Cube")


        result = []
        for prim in iter_prims:
            if prim != root_prim and prim.GetTypeName() == "Xform":
                prim.SetTypeName("Scope")
                result.append(prim)
        result.pop(0)
        # print(root_prim)

        # Time to check the file 

        # print(result)
        #let's check is the hierarchy structure is right 
        target_prims = ["geo", "mtl", "proxy", "render"]
        iter_names = iter(target_prims)
        x = 0
   
        # if any(prim in stage.Traverse() for prim in ["geo", "mtl", "proxy", "render"]):
        #     print("trouvé !")
        target_paths = [
            f"{root_path}/geo",
            f"/{asset_name}/geo/render",
            f"/{asset_name}/geo/proxy",
            f"/{asset_name}/mtl",
        ]
        # print(target_paths[3])
        print(len(target_paths))
        print(type(target_paths))
        # test = prim.GetPath()
        # for prim in stage.Traverse():
        #         # if prim.GetPath() == next():
        #     if any(test in stage.Traverse() for test in next(iter_names)):
        #         print(prim)
        #         result.append(prim)
        #     else:
        #         print("rien")

            # while x <= len(target_paths):
            #     if prim.GetTypeName() == "Xform" or "Scope" and prim.GetPath() == next(target_iter):
            #         x += 1
            #         print(prim)
        # x = enumerate(target_paths)
        # incr = next(x)        
        # for index, target_paths in enumerate(target_paths):      
        #     for prim in stage.Traverse():
        #         incr = next(x)[1]
        #         # while index <= len(target_paths):
        #         if prim.GetTypeName() == "Xform" or "Scope" and prim.GetPath() == incr:
        #             print(prim)
        #             result.append(prim)
        #             index += 1
        #         else: 
        #             index += 1
        #             print("pas de prim")
        #     pass
        # print(result)

        enum = enumerate(target_paths)
        result_paths = []
        incr = next(enum)[1]

        for index, target_paths in enumerate(target_paths):
            for prim in stage.Traverse():
                if prim.GetTypeName() == "Scope" or "Xform" and prim.GetPath() == target_paths:
                    print(prim)
                    #we need to use GetPath again to output a Sdf.Path() instead of a Usd python object
                    result_paths.append(prim.GetPath())
                    index +=1
                else: 
                    print("prim not corresponding")
                    index +=1
            break
        
        result_comp = []
        for path in result_paths:
            new_path = str(path).split("<")
            # print(type(new_path))
            result_comp.append("".join(new_path))

        target_paths = [
            f"{root_path}/geo",
            f"/{asset_name}/geo/render",
            f"/{asset_name}/geo/proxy",
            f"/{asset_name}/mtl",
        ]

        print(result_comp)
        print(target_paths)
        list1 = target_paths
        list2 = result_comp


        if len(list1) != len(list2):
            print("Elements missing")
            return False
        if sorted(list1) == sorted(list2):
            return True
        else: 
            return False
        

if __name__ == "__main__":
    pass
    # x = create_usd_asset_window()
    # x.show()