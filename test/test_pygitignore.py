import sys

print(sys.path)

from pygitignore import pygitignore

def test_match_001():
    pig = pygitignore.PyGitIgnore(open('test/001-pyignore', 'r').read())

    assert 0 == 0