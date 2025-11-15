import pyblish.api
import hou

from fireflies.houdini import abstract_hou_publish


class Extract_Commentary(pyblish.api.InstancePlugin):
    """Extract comment on publish """

    # order = pyblish.api.ExtractorOrder
    order = 1.2

    optional=True
    label="Export comment"

    def process(self, instance):
        context = instance.context
        comment = context.data.get('comment')

        node = instance.data.get('node')
        asset_name = node.evalParm('asset_name')

        abstract_publish = abstract_hou_publish.hou_publish()
        abstract_publish.write_commentary(text=comment, asset_name=asset_name)
