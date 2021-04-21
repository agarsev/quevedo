# 2020-04-10 Antonio F. G. Sevilla <afgs@ucm.es>

import os
import sys

from .test import test
from .library import DarknetNetwork


# Only way to suppress usual darknet output as much as possible
class DarknetShutup(object):

    def __enter__(self):
        self.stderr_fileno = sys.stderr.fileno()
        self.stderr_save = os.dup(self.stderr_fileno)
        self.stdout_fileno = sys.stdout.fileno()
        self.stdout_save = os.dup(self.stdout_fileno)
        self.devnull = open(os.devnull, 'w')
        devnull_fn = self.devnull.fileno()
        os.dup2(devnull_fn, self.stderr_fileno)
        os.dup2(devnull_fn, self.stdout_fileno)

    def __exit__(self, type, value, traceback):
        self.devnull.close()
        os.dup2(self.stderr_save, self.stderr_fileno)
        os.dup2(self.stdout_save, self.stdout_fileno)
        os.close(self.stderr_save)
        os.close(self.stdout_save)
