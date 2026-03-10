import pyblish.api 
import hou 

from fireflies.houdini import abstract_hou_publish

class Extract_Preview(pyblish.api.InstancePlugin):
    """Extract scene preview on publish"""

    order = 2.3

    optional=True
    label = "Export preview (single frame)"

    def process(self, instance):
        abstract_publish = abstract_hou_publish.hou_publish()

        preview_path = abstract_publish.export_preview(asset_name=instance.name)

        instance.data['preview'] = preview_path