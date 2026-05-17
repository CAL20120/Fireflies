import pyblish.api 

from fireflies.context import prod_tracker
KT_CONTEXT = prod_tracker.manage_context()

class CollectKtData(pyblish.api.ContextPlugin): 
    """Collect Kitsu Data / Session"""
    
    order = pyblish.api.CollectorOrder
    label = "Collect Kitsu Data"
    active=True
    optional=False


    def process(self, context):
        self.scene_path = context.data.get('scene_path')

        curr_context = KT_CONTEXT.get_full_ct(self.scene_path)

        curr_entity = curr_context['current_entity']
        entity_name = curr_entity['name']

        shot_name = None
        if not curr_context['is_asset']:
            print("### SHOT CONTEXT ###")

            shot_name = entity_name
            sequence_name = curr_entity['sequence_name']

            context.data['shot_name'] = shot_name
            context.data['sequence_name'] = sequence_name


        curr_entity = curr_context['current_entity']
        curr_task = curr_context['task_entity']

        context.data['current_entity'] = curr_entity
        context.data['current_task'] = curr_task

        if shot_name:
            context.data['is_shot'] = True