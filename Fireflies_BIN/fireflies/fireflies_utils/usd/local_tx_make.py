import os
import argparse
import subprocess

def make_tx(input_file:str):
    if not any(ext in input_file for ext in ['exr', 'png', 'jpeg', 'raw']):
        print("Please select an image in the right format")

    file_dir = os.path.dirname(input_file.replace("\\", "\\"))
    # path_tex = "{}.tex".format(file_dir)
    tex_path = f"{input_file.rsplit('.', 1)[0]}.tex"
    
    if os.path.exists(tex_path):
        return


    tx_make = "C:\\Program Files\\Pixar\\RenderManProServer-26.3\\bin\\txmake.exe"
    subprocess.Popen(
        [
            tx_make, 
            input_file,
            tex_path
        ],
        shell=True, stdout=subprocess.PIPE
    )

    print("tx file generated at {}".format(tex_path))

    return tex_path



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-input_file')
    args = parser.parse_args()

    make_tx(args.input_file)
    pass

main()