# *-* coding: utf-8 *-*
import argparse
import enum
import fnmatch
import os
import pathlib
import re
import sys
import zipfile
import zipapp


zipfile_regex = re.compile(r'([a-zA-Z0-9_]*)-([0-9.]*)\.zip')


class MatchResult(enum.Enum):
    NO_MATCH = 0
    IGNORED_DIR = 1  # special case: directory is not examined anymore
    IGNORED_FILE = 2
    EXPLICITE_INCLUDED = 3  # by using !...


class PyGitIgnore:

    dblAsterisks = "**"

    def __init__(self, ignore_patterns):
        self._patterns = ignore_patterns.replace('\r', '').split('\n')

    def print_patterns(self):
        for p in self._patterns:
            print(p)

    def add_include(self, pattern):
        self._patterns.append(pattern)

    def add_exclude(self, pattern):
        self._patterns.append('!' + pattern)

    def match(self, pattern: str, value: str) -> MatchResult:
        '''
        Match matches single pattern in the same manner that gitignore does.

        Reference https://git-scm.com/docs/gitignore.

        '''

        # strip leading and trailing whitespace
        pattern = pattern.strip()

        # A blank line matches no files, so it can serve as a separator for readability.
        if pattern == '':
            return MatchResult.NO_MATCH

        # A line starting with # serves as a comment. Put a backslash ("\") in front of the first hash for patterns that begin with a hash.
        if pattern.startswith('#'):
            return MatchResult.NO_MATCH

        negate = True if pattern[0] == '!' else False
        if negate:
            pattern = pattern[1:].strip()

        is_dir = True if pattern[-1] == '/' else False

        # todo: replace '[...]' expressions

        root_only = False

        if pattern.startswith('**/'):
            root_only = False
            pattern = pattern.replace('**/', '')
        else:
            if pattern.startswith('/'):
                root_only = True
                pattern = pattern[1:]

            if pattern.endswith('/'):
                if pattern[:-1].find('/') != -1:
                    root_only = True
            else:
                if pattern.find('/') != -1:
                    root_only = True

        value = value.as_posix()

        path_parts = value.split('/')
        pathlen = len(path_parts)
        pattern_ = pathlib.PurePath(pattern).as_posix()
        pattern_parts = pattern_.split('/')
        patternlen = len(pattern_parts)
        if patternlen > pathlen:
            return MatchResult.NO_MATCH

        matched = False
        if pathlen == 1:
            if is_dir:
                return MatchResult.NO_MATCH
            else:
                if pathlib.PurePath(path_parts[0]).match(pattern_parts[0]):
                    matched = True
        else:
            pathpart_start_index = 0
            path_part_endindex = 0 if root_only else pathlen - \
                patternlen - (1 if is_dir else 0)
            possible_match = False
            for i in range(pathpart_start_index, path_part_endindex + 1):
                for j in range(patternlen):
                    if pathlib.PurePath(path_parts[i + j]).match(pattern_parts[j]):
                        possible_match = True
                        continue  # inner for loop
                    else:
                        possible_match = False
                        break  # inner for loop
                if possible_match:
                    # full pattern matched
                    break
            if possible_match:
                matched = True

        if matched:
            if negate:
                return MatchResult.EXPLICITE_INCLUDED
            else:
                return MatchResult.IGNORED_DIR if is_dir else MatchResult.IGNORED_FILE
        else:
            return MatchResult.NO_MATCH

        result = fnmatch.fnmatch(value, pattern)
        if result:
            if negate:
                return MatchResult.EXPLICITE_INCLUDED
            else:
                if is_dir:
                    return MatchResult.IGNORED_DIR
                else:
                    return MatchResult.IGNORED_FILE
        return MatchResult.NO_MATCH

    def _eval_dbl_asterisk(self, pattern, value):
        return False

    def flist(self, sourcedir):
        parent = pathlib.Path(sourcedir)
        for realpath in pathlib.Path(sourcedir).rglob('*'):
            if realpath.is_dir():
                # only return files, not dirs
                continue
            path = realpath.relative_to(parent)
            ignored_file = False
            for p in self._patterns:
                match_result = self.match(p, path)
                if match_result == MatchResult.IGNORED_DIR:
                    ignored_file = True
                    break
                if match_result == MatchResult.IGNORED_FILE:
                    ignored_file = True
                    continue
                if match_result == MatchResult.EXPLICITE_INCLUDED:
                    ignored_file = False
                    break
            if not ignored_file:
                file_include = True
            else:
                file_include = False
            if file_include:
                yield path

    def package_filter(self, path):
        file_include = True
        ignored_file = False
        for p in self._patterns:
            match_result = self.match(p, path)
            if match_result == MatchResult.IGNORED_DIR:
                file_include = False
                break
            if match_result == MatchResult.IGNORED_FILE:
                ignored_file = True
                continue
            if match_result == MatchResult.EXPLICITE_INCLUDED:
                file_include = True
                break
        if not ignored_file:
            file_include = True
        else:
            file_include = False
        return file_include


def main():
    my_parser = argparse.ArgumentParser(
        description='pygitignore - python implementation of .gitignore logic')
    # Add the arguments
    my_parser.add_argument('--ignorefile', '-i',
                           default='./.gitignore',
                           type=str,
                           help='file with ignore patterns')
    my_parser.add_argument('--sourcedir', '-s',
                           type=str,
                           help='root folder for applying ignore patterns')

    # Execute the parse_args() method
    args = my_parser.parse_args()
    #ignorefile = os.path.abspath(getattr(args, 'ignorefile'))
    ignorefile = pathlib.Path(getattr(args, 'ignorefile'))
    if not ignorefile.is_file():
        raise ValueError('ignorefile %s doesn not exist', ignorefile)
    sourcedir = getattr(args, 'sourcedir')
    if sourcedir is None:
        #sourcedir = os.path.dirname(ignorefile)
        sourcedir = ignorefile.parent
    if not sourcedir.is_dir():
        raise ValueError('sourcedir %s does not exist', sourcedir)

    pgi = PyGitIgnore(ignore_patterns=open(ignorefile, 'r').read())

    for f in pgi.flist(sourcedir):
        pass

    # match = zipfile_regex.match(source)
    # if match:
    #     modulename = match.groups()[0] if modulename is None else modulename
    #     version = match.groups()[1]
    #     if os.path.isfile(source):
    #         assume zipfile
    #         zip_subdir = modulename + '-' + version + '/'
    #         print(modulename, version, zip_subdir)
    #         pf = PackageFilter(modulename='src')
    #         for fileinfo in (f for f in zipfile.ZipFile(source).filelist
    #                          if str(f.filename).startswith(zip_subdir)):
    #             mark = '-' if pf.package_filter(
    #                 str(fileinfo.filename).replace(zip_subdir, '')) else '+'

    #             if fileinfo.is_dir():
    #                 print(mark, 'folder:', fileinfo.filename)
    #             else:
    #                 print(mark, 'file:', fileinfo.filename)

    # elif os.path.isdir(source):
    #     assume folder
    #     pass


if __name__ == '__main__':
    main()
