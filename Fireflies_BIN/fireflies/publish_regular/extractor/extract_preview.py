import pyblish.api 

from fireflies.context.prod_tracker import CT_HOU, CT_MAYA


class Extract_Preview(pyblish.api.InstancePlugin):
    """Extract scene preview on publish"""

    order = 2.3

    optional=True
    label = "Export preview (single frame)"

    def process(self, instance):
        context = instance.context

        if CT_HOU:
            from fireflies.houdini import abstract_hou_publish

            abstract_publish = abstract_hou_publish.hou_publish()
            preview_path = abstract_publish.export_preview(asset_name=instance.name)


        if CT_MAYA: 
            from fireflies.publish_regular import abstract_publish as ab

            shot_status = context.data.get('is_shot')
            if shot_status:
                target_name = context.data.get('shot_publish_name')

            else:
                target_name = instance.name
            
            preview_path = ab.export_preview(asset_name=target_name)

        instance.data['preview'] = preview_path