#!/Users/jpierel/anaconda3/envs/astro2/bin python2

NORMAL = 0    # use python zip libraries
PROCESS = 1   # use (zcat, gzip) or (bzcat, bzip2)
PARALLEL = 2  # (pigz -dc, pigz) or (pbzip2 -dc, pbzip2)

def anyOpen(filename, mode='r', buff=1024*1024, external=PARALLEL):
    if 'r' in mode and 'w' in mode:
        return None
    if filename.startswith('!'):
        import subprocess
        if 'r' in mode:
            return subprocess.Popen(filename[1:], shell=True, bufsize=buff,
                                    stdout=subprocess.PIPE).stdout
        elif 'w' in mode:
            return subprocess.Popen(filename[1:], shell=True, bufsize=buff,
                                    stdin=subprocess.PIPE).stdin
    elif filename.endswith('.bz2'):
        if external == NORMAL:
            import bz2
            return bz2.BZ2File(filename, mode, buff)
        elif external == PROCESS:
            if not which('bzip2'):
                return anyOpen(filename, mode, buff, NORMAL)
            if 'r' in mode:
                return anyOpen('!bzip2 -dc ' + filename, mode, buff)
            elif 'w' in mode:
                return anyOpen('!bzip2 >' + filename, mode, buff)
        elif external == PARALLEL:
            if not which('pbzip2'):
                return anyOpen(filename, mode, buff, PROCESS)
            if 'r' in mode:
                return anyOpen('!pbzip2 -dc ' + filename, mode, buff)
            elif 'w' in mode:
                return anyOpen('!pbzip2 >' + filename, mode, buff)
    elif filename.endswith('.gz'):
        if external == NORMAL:
            import gzip
            return gzip.GzipFile(filename, mode, buff)
        elif external == PROCESS:
            if not which('gzip'):
                return anyOpen(filename, mode, buff, NORMAL)
            if 'r' in mode:
                return anyOpen('!gzip -dc ' + filename, mode, buff)
            elif 'w' in mode:
                return anyOpen('!gzip >' + filename, mode, buff)
        elif external == PARALLEL:
            if not which('pigz'):
                return anyOpen(filename, mode, buff, PROCESS)
            if 'r' in mode:
                return anyOpen('!pigz -dc ' + filename, mode, buff)
            elif 'w' in mode:
                return anyOpen('!pigz >' + filename, mode, buff)
    elif filename.endswith('.xz'):
        if which('xz'):
            if 'r' in mode:
                return anyOpen('!xz -dc ' + filename, mode, buff)
            elif 'w' in mode:
                return anyOpen('!xz >' + filename, mode, buff)
    else:
        return open(filename, mode, buff)
    return None

def which(program):
    import os
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None