#!/usr/bin/python
import sys
sys.path.insert(0, '/mnt/raid/home/dewoller/mydoc/research/digitalAssessment/code')

import calculateMark
import xls2dict
import pandas as pd

def allEqual( s, t) :
   return [x==y for x, y in zip(s, t)].all()

def test_findSlice():
    #''' testing reader '''
    reader=xls2dict.Reader("tests/modelAnswer.xlsx") 
    modelAnswer=reader.dfs[0]
    marker=calculateMark.Marker(modelAnswer)
#    assert(list( marker.findSlice( pd.Series(["a"]), pd.Series(["a"]))) == ["a"])
#    assert(list( marker.findSlice( pd.Series(["a","b", "c", "d", "e", "f", "g"]), pd.Series(["a"]))) == ["a"])



