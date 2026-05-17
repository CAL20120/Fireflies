import pyblish.api 
import os

from fireflies.publish_regular import abstract_publish as ab

from fireflies.context.prod_tracker import CT_HOU, CT_MAYA

class Kt_Integrate_Preview(pyblish.api.InstancePlugin):
    """Add a video the the related asset on kitsu"""

    order = 3.1
    optional = True
    active = False
    label = "Kitsu - Add Video Preview"

    def process(self, instance):
        context = instance.context

        asset_name = instance.name
        scene_path = context.data.get('scene_path')

        asset_family = instance.data.get('family')

        if context.data.get('is_shot') and CT_MAYA and asset_family == "shot_dependency":
            asset_name = context.data.get('shot_publish_name')
        
    
        video_preview_path = ab.export_video_preview(asset_name=asset_name, scene_path=scene_path)

        print("### video preview: {} ###".format(video_preview_path))

        instance.data['video_preview_path'] = video_preview_path