import pyblish.api

from maya import cmds

class ValidateHierarchy(pyblish.api.InstancePlugin):
    """
    USD hierarchy
    Check is the hierarchy is correct (no missing transforms, names)
    """

    order = pyblish.api.ValidatorOrder
    label = "Asset hierarchy"
    optional=True

    def process(self, instance):
        checker = check_usd_hierarchy.usd_check_hierarchy()
        # print(instance[0])

        if checker.export_usd_check(asset_name=instance[0]) == False:
            raise pyblish.api.ValidationError("Wrong hierarchy")
        # pass

    