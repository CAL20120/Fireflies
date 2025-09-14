import os
from fireflies_utils import utils

#TODO ajouter le fetch du nom du repo git pour éviter d'avoir un hard link

class update_from_git():
    def __init__(self):
        super(update_from_git, self).__init__()
        git_name= ""
        self.target_directory_cmd = "\\" + git_name

        self.git_link = "https://github.com/CAL20120/Sync_Test.git"
        main_dir = __file__.rsplit("\\", 2)
        self.target_directory = r"\Sync_Test" ##insert repo main folder or folder used to store git files
        self.current_dir = main_dir[0]
     
    def check_exists(self):
        found = True
        if (os.path.exists(self.current_dir + self.target_directory)):
            return found
        if not found:
            print("Error : no folder")

    def launch_sync(self):
        
        if not self.check_exists():
            os.system(
                f"pushd {self.current_dir} && git clone {self.git_link}"
            )
            print("\n Sync successful")
            utils.print_main_name(self)
        
        else: 
            os.system(
                f"pushd {self.current_dir + self.target_directory} && git pull {self.git_link}"
            )
            print("Up to date !")
            utils.print_main_name(self)


def main():
    updater = update_from_git()
    updater.launch_sync()

main()

