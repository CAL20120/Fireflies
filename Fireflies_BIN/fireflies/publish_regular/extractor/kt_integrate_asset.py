import pyblish.api 
import os

from fireflies.context import prod_tracker

class Kt_Integrate_Asset(pyblish.api.InstancePlugin):
    """Add asset and metadate to Kitsu"""

    order = 3.2
    optional = False
    active = False
    label = "Kitsu - Add / Update Asset"

    def process(self, instance):
        context = instance.context
        comment = context.data.get('comment')

        props_check = context.data.get('props_check')

        print("DEBUG KITSU PROPS: {}".format(props_check))

        video_preview_path = instance.data.get('video_preview_path')

        if video_preview_path:
            preview_path = video_preview_path

        else:
            preview_path = instance.data.get('preview')
        
        scene_path = context.data.get('scene_path')

        asset_name = instance.name

        kt_CONTEXT = prod_tracker.manage_context()

        if props_check:
            kt_CONTEXT.publish_asset_task(asset_name, scene_path, preview_path, comment)
            return

        kt_CONTEXT.publish_shot_task(comment, preview_path, scene_path)