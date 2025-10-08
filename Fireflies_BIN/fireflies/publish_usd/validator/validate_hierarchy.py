import pyblish.api
from fireflies.fireflies_utils.usd.utils import check_usd_hierarchy
from maya import cmds

class ValidateHierarchy(pyblish.api.InstancePlugin):
    """
    USD hierarchy
    Check is the hierarchy is correct (no missing transforms, names)
    """

    order = pyblish.api.ValidatorOrder
    label = "Check Asset hierarchy"
    optional=True

    def process(self, instance):
        checker = check_usd_hierarchy.usd_check_hierarchy()
        # print(instance[0])

        if checker.export_usd_check(asset_name=instance[0]) is not True:
            raise pyblish.api.ValidationError("Wrong hierarchy")
        # pass

    