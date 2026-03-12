import pyblish.api 
import os

from fireflies.houdini import abstract_hou_publish

PUBLISH = abstract_hou_publish.hou_publish()
class Kt_Integrate_Preview(pyblish.api.InstancePlugin):
    """Add a video the the related asset on kitsu"""

    order = 3.1
    optional = True
    active = False
    label = "Kitsu - Add Video Preview"

    def process(self, instance):
        pyblish_context = instance.context

        asset_name = instance.name
        scene_path = pyblish_context.data.get('scene_path')

        video_preview_path = PUBLISH.export_video_preview(asset_name, scene_path)
        print("### video preview: {} ###".format(video_preview_path))

        instance.data['video_preview_path'] = video_preview_path