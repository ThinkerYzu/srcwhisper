import os
from django.conf import settings

BLACK_LIST = ['.git']

class SourceService(object):
    def __init__(self):
        super().__init__()
        self.root = settings.WHISPER_REPO_PATH
        self.root_user_code = settings.USER_CODE_REPO
        pass

    def get_ucode_path(self, path):
        hashcode = path.replace(':ucode:/', '', 1)
        fullpath = os.path.join(self.root_user_code, hashcode)
        fullpath = os.path.abspath(fullpath)
        return fullpath

    def is_file(self, path):
        if path.startswith(':ucode:'):
            fullpath = self.get_ucode_path(path)
            if not fullpath.startswith(self.root_user_code):
                return False
            return os.path.exists(self.get_ucode_path(path))

        fullpath = os.path.join(self.root, path)
        fullpath = os.path.abspath(fullpath)
        if not fullpath.startswith(self.root):
            return False
        st = os.stat(fullpath)
        mode = st[0]
        ft = mode & 0o170000
        return ft == 0o100000

    def is_dir(self, path):
        if path.startswith(':ucode:'):
            return False

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
        if not self.is_dir(path):
            return None

        fullpath = os.path.join(self.root, path.strip('/'))
        fullpath = os.path.abspath(fullpath)
        if not fullpath.startswith(self.root):
            return None
        dir_list = [x
                    for x in os.listdir(fullpath)
                    if x not in BLACK_LIST]
        dirs = filter(lambda x: self.is_dir(os.path.join(fullpath, x)),
                      dir_list)
        files = filter(lambda x: self.is_file(os.path.join(fullpath, x)),
                       dir_list)
        fullpath = os.path.join(self.root, path.strip('/'))
        fullpath = os.path.abspath(fullpath)
        return list(dirs), list(files), fullpath.replace(self.root, '', 1).strip('/')

    def abs(self, path):
        if path.startswith(':ucode:/'):
            fullpath = self.get_ucode_path(path)
        else:
            fullpath = os.path.join(self.root, path)
            fullpath = os.path.abspath(fullpath)
            pass
        return fullpath

    def get_basename(self, path):
        if path.startswith(':ucode:'):
            fn = self.abs(path)
            fo = open(fn)
            fn = fo.readline().strip('\n')
            return os.path.basename(fn)
        return os.path.basename(path)

    def get_dirname(self, path):
        if path.startswith(':ucode:'):
            return ''
        return os.path.dirname(path)

    def get_rel_url(self, path):
        if path.startswith(':ucode:'):
            return path

        fullpath = os.path.join(self.root, path.strip('/'))
        fullpath = os.path.abspath(fullpath)
        return fullpath.replace(self.root, '', 1).strip('/')

    def open_file(self, path):
        if not self.is_file(path):
            return None
        if path.startswith(':ucode:'):
            fo = open(self.abs(path))
            fo.readline()
            return fo
        return open(self.abs(path))
    pass
