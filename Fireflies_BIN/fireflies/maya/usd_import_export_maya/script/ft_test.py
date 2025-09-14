import os
from cgev.pipeline.data import session
import ftrack_api

context = session.getContext()
project = context.getProjectName()
sequence = context.getSequenceName()
shot = context.getShotName()

task = context.getTaskName()
task_id = context.getTaskId()

print(task)
print(task_id)
