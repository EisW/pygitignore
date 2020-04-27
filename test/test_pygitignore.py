from pygitignore import pygitignore
import pathlib
import pytest
import sys


#patterntestlist = ['{:03d}'.format(i) for i in range(19) if i not in [1,2, 16]]
patterntestlist = ['{:03d}'.format(i) for i in range(19)]

@pytest.mark.parametrize('patterntest', patterntestlist)
def test_match(patterntest):
    ignorepatterns = open('test/' + patterntest + '-pyignore', 'r').read()
    pig = pygitignore.PyGitIgnore(ignorepatterns)
    reflist = [pathlib.Path(refname.strip()) for refname in open(
        'test/' + patterntest + '-included', 'r').readlines()]
    neglist = [pathlib.Path(refname.strip()) for refname in open(
        'test/' + patterntest + '-excluded', 'r').readlines()]
    testlist = list(pig.flist('test/root'))
    reflist_set = set([str(p) for p in reflist])
    testlist_set = set([str(p) for p in testlist])
    more_refs = reflist_set - testlist_set
    less_refs = testlist_set - reflist_set
    assert reflist_set == testlist_set
    count = 0
    for count, path in enumerate(testlist, 1):
        assert path in reflist
        assert path not in neglist
    refcount = len(reflist)
    assert count == refcount
