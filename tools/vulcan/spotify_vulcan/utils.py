import os
import stat

def del_ro(action, name, exc):
    os.chmod(name, 0777)
    try:
        action(name)
    except:
        os.chmod(os.path.abspath(os.path.join(name, os.pardir)), 0777)
        action(name)
