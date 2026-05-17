import pyblish.api

from fireflies.context.prod_tracker import CT_HOU, CT_MAYA

from fireflies.publish_regular import abstract_publish as ab 


class Extract_Commentary(pyblish.api.InstancePlugin):
    """Extract comment on publish """

    order = 2.2
    optional=True
    label="Export comment"

    def process(self, instance):
        context = instance.context
        comment = context.data.get('comment')

        shot_status = context.data.get('is_shot')

        target_name = instance.name

        if shot_status and CT_MAYA:
            target_name = context.data.get('shot_publish_name')

        print(target_name)

        ab.write_commentary(comment, target_name)


        # node = instance.data.get('node')
        # asset_name = node.evalParm('asset_name')

        # if CT_HOU:
        #     abstract_publish = abstract_hou_publish.hou_publish()
        #     abstract_publish.write_commentary(text=comment, asset_name=instance.name)

        # if CT_MAYA:
        #     abstract_publish = abstract_maya_publish.maya_regular_publish()

        