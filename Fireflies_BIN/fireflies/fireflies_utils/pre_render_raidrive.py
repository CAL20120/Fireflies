import os

def __main__(*args): 
    open_usd_dir()

def open_usd_dir(*args): 
    target_dir = os.environ.get('NAS_USD_DIR')
    
    if not target_dir:
        raise FileExistsError("### Couldn't open the usd folder ###")

    os.startfile(target_dir)


if __name__ == '__main__':
    __main__()