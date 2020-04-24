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

    def match(self, pattern: str, value: pathlib.Path) -> MatchResult:
        '''
        Match matches single pattern in the same manner that gitignore does.

        Reference https://git-scm.com/docs/gitignore.

        '''
        value = value.as_posix()
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

        # Two consecutive asterisks ("**") in patterns matched
        # against full pathname may have special meaning:
        if pattern.find(self.dblAsterisks) != -1:
            raise ValueError('double asterisk not supported yet')
            if pathlib.Path(value).match(pattern):
                pmatch = True
            else:
                pmatch = False
            res = not pmatch if negate else pmatch
            if res:
                if is_dir:
                    return MatchResult.IGNORED_DIR
                else:
                    return MatchResult.IGNORED_FILE
            else:
                return MatchResult.EXPLICITE_INCLUDED

        # If the pattern does not contain a slash /, Git treats it as a shell glob
        # pattern and checks for a match against the pathname relative to the location
        # of the .gitignore file (relative to the toplevel of the work tree if not from
        # a .gitignore file).
        #result = fnmatch.fnmatch(value.split('/')[-1], pattern)
        matched = False

        if (pattern.startswith('/') or
            pattern[-1] != '/' and pattern.find('/') != -1):
            parentpat = './'
        else:
            parentpat = '**/'
        subpattern = [pathlib.PurePath(parentpat + pattern + '/**')]
        if not is_dir:
            subpattern.append(pathlib.PurePath(parentpat + pattern))

        for pat in subpattern:
            if fnmatch.fnmatch(value, pat):
            #if pathlib.PurePosixPath(value).match(pat):
                matched = True
                break

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
        for path in pathlib.Path(sourcedir).rglob('*'):
            if path.is_dir():
                # only return files, not dirs
                continue
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
                yield path.relative_to(sourcedir)

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
