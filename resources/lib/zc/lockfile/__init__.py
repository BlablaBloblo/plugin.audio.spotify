##############################################################################
#
# Copyright (c) 2001, 2002 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

import os
import logging

logger = logging.getLogger("zc.lockfile")


class LockError(Exception):
    """Couldn't get a lock
    """


try:
    import fcntl
except ImportError:
    try:
        import msvcrt
    except ImportError:
        def _lock_file():
            raise TypeError('No file-locking support on this platform')


        def _unlock_file():
            raise TypeError('No file-locking support on this platform')

    else:
        # Windows
        def _lock_file(file):
            # Lock just the first byte
            try:
                msvcrt.locking(file.fileno(), msvcrt.LK_NBLCK, 1)
            except IOError:
                raise LockError("Couldn't lock %r" % file.name)


        def _unlock_file(file):
            try:
                file.seek(0)
                msvcrt.locking(file.fileno(), msvcrt.LK_UNLCK, 1)
            except IOError:
                raise LockError("Couldn't unlock %r" % file.name)

else:
    # Unix
    _flags = fcntl.LOCK_EX | fcntl.LOCK_NB


    def _lock_file(file):
        try:
            fcntl.flock(file.fileno(), _flags)
        except IOError:
            raise LockError("Couldn't lock %r" % file.name)


    def _unlock_file(file):
        fcntl.flock(file.fileno(), fcntl.LOCK_UN)


class LazyHostName(object):
    """Avoid importing socket and calling gethostname() unnecessarily"""

    def __str__(self):
        import socket
        return socket.gethostname()


class LockFile:
    _fp = None

    def __init__(self, path, content_template='{pid}'):
        self._path = path
        try:
            # Try to open for writing without truncation:
            fp = open(path, 'r+')
        except IOError:
            # If the file doesn't exist, we'll get an IO error, try a+
            # Note that there may be a race here. Multiple processes
            # could fail on the r+ open and open the file a+, but only
            # one will get the the lock and write a pid.
            fp = open(path, 'a+')

        try:
            _lock_file(fp)
        except:
            fp.close()
            raise

        # We got the lock, record info in the file.
        self._fp = fp
        fp.write(" %s\n" % content_template.format(pid=os.getpid(),
                                                   hostname=LazyHostName()))
        fp.truncate()
        fp.flush()

    def close(self):
        if self._fp is not None:
            _unlock_file(self._fp)
            self._fp.close()
            self._fp = None
