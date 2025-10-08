import pyblish.api 
from fireflies.maya import usd_build_path

class Usd_Extractor_Maya(pyblish.api.InstancePlugin):
    """Publish usd file"""

    order = pyblish.api.ExtractorOrder
    optional=True
    label="Extract Usd data"

    def process(self, instance):
        asset = instance[0]
        exporter = usd_build_path.maya_to_usd(asset_name=asset)
        exporter.publish_usd()