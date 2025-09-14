import os
from cgev.pipeline.data import session
import ftrack_api

context = session.getContext()
project = context.getProjectName()
sequence = context.getSequenceName()
shot = context.getShotName()
task = context.getTaskName()
task_id = context.getTaskId()
print(task_id)

manager = session.getManager()
print(manager.getShot(project, sequence, shot).getPath())

sessionFT = session.getSessionFT()

query = f"select name from Task where id is {task_id}"
task_ft = sessionFT.query(query).first()
# for key in result.keys():
#     print(key, result[key])


asset_name = "usd.toto"

# - On cherche si l'asset existe dejà
query_asset = (
    f"Asset where name is '{asset_name}' and parent.id is {context.getShotId()}"
)
asset_ft = sessionFT.query(query_asset).first()

if asset_ft == None:
    # - On doit creer l'asset

    query = 'AssetType where name is "{}"'.format("Usd Layer")
    asset_type = sessionFT.query(query).first()

    query = f"Shot where id is {context.getShotId()}"
    shot_ft = sessionFT.query(query).first()

    asset_ft = sessionFT.create(
        "Asset",
        {
            "name": asset_name,
            "type": asset_type,
            "parent": shot_ft,
        },
    )

query = "User where username is clucas"
user_ft = sessionFT.query(query).first()

version_ft = sessionFT.create(
    "AssetVersion",
    {
        "asset": asset_ft,
        "task": task_ft,
        "comment": "zero plus zero egal la tete a toto",
        "user": user_ft,
    },
)


# - On popule la version

query = 'Location where name is "ftrack.unmanaged"'
location = sessionFT.query(query).first()

asset_path = "//chemin/ver/lasset/usd.usd"

component = version_ft.create_component(
    path=asset_path, data={"name": "main"}, location=location
)

version_ft["custom_attributes"]["linkedto"] = os.path.basename(asset_path)

try:
    sessionFT.commit()
    print("commit")
except:
    print("rollback")
    sessionFT.rollback()
