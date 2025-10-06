import os
import pyblish.api


class CollectMayaGeometry(pyblish.api.ContextPlugin):
    """Collect all geo in the scene"""

    order = pyblish.api.CollectorOrder - 0.5
    label = "Maya geometry"

    hosts = ["maya"]
    version = (0, 1, 0)

    active = True


    def process(self, context):
        import os
        from maya import cmds

        sets = cmds.ls(type="objectSet", long=True)
        geo_sets = [geo_set for geo_set in sets if geo_set.endswith("_GEO")]

        asset_candidates = cmds.ls("*_ASSET", type="transform")
        print(cmds.nodeType(asset_candidates))
        # log.debug("Geo assets candidates : {}".format("\n".join(asset_candidates)))

        for asset_candidate in asset_candidates:
            #if we use the first xform in the hierarchy it returns None if we get the children here
            asset_name = cmds.listRelatives(asset_candidate, children=True)
            # asset_name = asset_candidates
            if cmds.nodeType(asset_candidate) != "transform":
                continue
            instance = context.create_instance(asset_candidate)
            # instance = pyblish.api.Instance(name="MAYA_USD")
            instance.data["asset_name"] = asset_candidate
            instance.append("asset_name")
            instance.data["family"] = "geometry"
            instance.data["usd_ext"] = ".usda"
            instance[0] = asset_candidate

        for instance in context:
            self.log.debug(f"######{instance}")
            self.log.debug(str(instance))
        
