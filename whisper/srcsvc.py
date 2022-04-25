import os
from django.conf import settings

BLACK_LIST = ['.git']

class SourceService(object):
    def __init__(self):
        super().__init__()
        self.root = settings.WHISPER_REPO_PATH
        pass

    def is_file(self, path):
        fullpath = os.path.join(self.root, path)
        fullpath = os.path.abspath(fullpath)
        if not fullpath.startswith(self.root):
            return None
        st = os.stat(fullpath)
        mode = st[0]
        ft = mode & 0o170000
        return ft == 0o100000

    def is_dir(self, path):
        fullpath = os.path.join(self.root, path)
        fullpath = os.path.abspath(fullpath)
        if not fullpath.startswith(self.root):
            return None
        st = os.stat(fullpath)
        mode = st[0]
        ft = mode & 0o170000
        return ft == 0o40000

    def is_valid(self, path):
        return self.is_dir(path) or self.is_file(path)

    def list(self, path):
        fullpath = os.path.join(self.root, path.strip('/'))
        fullpath = os.path.abspath(fullpath)
        if not fullpath.startswith(self.root):
            return None
        if not self.is_dir(fullpath):
            return None
        dir_list = [x
                    for x in os.listdir(fullpath)
                    if x not in BLACK_LIST]
        dirs = filter(lambda x: self.is_dir(os.path.join(fullpath, x)),
                      dir_list)
        files = filter(lambda x: self.is_file(os.path.join(fullpath, x)),
                       dir_list)
        return list(dirs), list(files), fullpath.replace(self.root, '', 1).strip('/')

    def abs(self, path):
        fullpath = os.path.join(self.root, path)
        fullpath = os.path.abspath(fullpath)
        return fullpath
    pass
