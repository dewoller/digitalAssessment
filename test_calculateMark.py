#!/usr/bin/python
#import sys
#sys.path.insert(0, '/mnt/raid/home/dewoller/mydoc/research/digitalAssessment/code')

import calculateMark
import xls2dict
import pandas as pd

def allEqual( s, t) :
   return [x==y for x, y in zip(s, t)].all()

def test_findSlice():
    #''' testing reader '''
    marker=calculateMark.Marker()
    assert(list( marker.findSlice( pd.Series(["a"]), pd.Series(["a"]))) == ["a"])
    assert(list( marker.findSlice( pd.Series(["a","b", "c", "d", "e", "f", "g"]), pd.Series(["a"]))) == ["a"])

    assert(list( marker.findSlice( pd.Series(["a","b", "c", "d", "e", "f", "g"]), pd.Series(["d",'f', 'g']))) ==["d",'f', 'g'] )
    assert(list( marker.findSlice( pd.Series(["a","b", "c", "d", "e", "f", "g"]), pd.Series(["f",'d', 'g']))) ==["d",'f', 'g'] )
    assert(list( marker.findSlice( pd.Series(["a","b", "c", "d", "e", "f", "g"]), pd.Series(["a", 'c']))) ==["a", 'c'] )
    assert(list( marker.findSlice( pd.Series(["a","b", "c", "d", "e", "f", "g"]), pd.Series(["c", 'e']))) ==["c", 'e'] )
    assert(list( marker.findSlice( pd.Series(["a","b", "c", "d", "e", "f", "g"]), pd.Series(["e", 'g']))) ==["e", 'g'] )
    assert(list( marker.findSlice( pd.Series(["a","b", "c", "d", "e", "f", "g"]), pd.Series(["a", "b", 'd']))) ==["a", "b", 'd'] )
    assert(list( marker.findSlice( pd.Series(["a","b", "c", "d", "e", "f", "g"]), pd.Series(["a", "c", 'd']))) ==["a", "c", 'd'] )
    assert(list( marker.findSlice( pd.Series(["a","b", "c", "d", "e", "f", "g"]), pd.Series(["a","b", "c", "d", "e", "f", "g"]))) ==["a","b", "c", "d", "e", "f", "g"] )
    assert(list( marker.findSlice( pd.Series(["a","b", "c", "d", "e", "f", "g"]), pd.Series(["a","b", "c", "d", "e", "g"]))) ==["a","b", "c", "d", "e", "g"] )
    assert(list( marker.findSlice( pd.Series(["a","b", "c", "d", "e", "f", "g"]), pd.Series(["a","b", "c", "d", "e", "f"]))) ==["a","b", "c", "d", "e", "f"] )
    assert(list( marker.findSlice( pd.Series(["a","b", "c", "d", "e", "f", "g"]), pd.Series(["a", "c", "d", "e", "f", "g"]))) ==["a", "c", "d", "e", "f", "g"] )
    assert(list( marker.findSlice( pd.Series(["a","b", "c", "d", "e", "f", "g"]), pd.Series(["b", "c", "d", "e", "f", "g"]))) ==["b", "c", "d", "e", "f", "g"] )
    assert(list( marker.findSlice( pd.Series(["a","b", "c", "d", "e", "f", "g"]), pd.Series(["Z", "c", "d", "e", "f", "g"]))) ==["c", "d", "e", "f", "g"] )
    assert(list( marker.findSlice( pd.Series(["a","b", "c", "d", "e", "f", "g"]), pd.Series(["a", "a", 'a']))) ==["a"] )
    assert(list( marker.findSlice( pd.Series(['a', 'b', 'c']), pd.Series(["a", "b","c"]))) ==["a", "b","c"] )
    assert(list( marker.findSlice( pd.Series(["Z", 'a', 'b', 'c', 'd']), pd.Series(["a", "b","c"]))) ==["a", "b","c"] )
    assert(list( marker.findSlice( pd.Series(["a","b", "c", "d", "e", "f", "g"]), pd.Series(["a","b"]))) ==["a","b"] )
    assert(list( marker.findSlice( pd.Series(["a","b", "c", "d", "e", "f", "g"]), pd.Series(["a"]))) ==["a"] )
    assert(list( marker.findSlice( pd.Series(["a","b", "c", "d", "e", "f", "g"]), pd.Series(["b"]))) ==["b"] )
    assert(list( marker.findSlice( pd.Series(["a","b", "c", "d", "e", "f", "g"]), pd.Series(["c"]))) ==["c"] )
    

def test_markUnorderedGroups():
    marker=calculateMark.Marker()
    reader=xls2dict.Reader("tests/modelAnswer.xlsx", isSubmission=False) 
    modelAnswer=reader.dfs['Q1']
    marker.prepareAnswer( modelAnswer )
    reader=xls2dict.Reader("tests/testSubmission.xlsx") 
    modelSubmission=reader.dfs['Q1']
    submission=marker.findGroups( modelSubmission )
    submission=marker.markUnorderedGroups(submission)
    assert( list( submission.Grouping ) == [u'P', None, u'B', None, u'A', u'A', u'A', u'A', None, u'L', None, u'L', None])

def test_markIntraGroupOrder():
    marker=calculateMark.Marker()
    reader=xls2dict.Reader("tests/modelAnswer.xlsx", isSubmission=False) 
    modelAnswer=reader.dfs['Q1']
    marker.prepareAnswer( modelAnswer )
    reader=xls2dict.Reader("tests/testSubmission.xlsx") 
    modelSubmission=reader.dfs['Q1']
    submission=marker.findGroups( modelSubmission )
    submission=marker.markIntragroupOrder(submission)
    assert( list( submission.Grouping ) == [u'P', None, u'B', None, u'A', u'A', u'A', u'A', None, u'L', None, u'L', None])

def test_markGroupOrder():
    marker=calculateMark.Marker()
    reader=xls2dict.Reader("tests/modelAnswer.xlsx", isSubmission=False) 
    modelAnswer=reader.dfs['Q1']
    marker.prepareAnswer( modelAnswer )
    reader=xls2dict.Reader("tests/testSubmission.xlsx") 
    modelSubmission=reader.dfs['Q1']
    submission=marker.findGroups( modelSubmission )
    submission=marker.markGroupOrder(submission)
    assert( list( submission.Grouping ) == [u'P', None, u'B', None, u'A', u'A', u'A', u'A', None, u'L', None, u'L', None])

def test_markUnspecifiedPositions():

    marker=calculateMark.Marker()
    reader=xls2dict.Reader("tests/modelAnswer1.xlsx", isSubmission=False) 
    modelAnswer=reader.dfs['Q1']
    marker.prepareAnswer( modelAnswer )
    reader=xls2dict.Reader("tests/testSubmission1.xlsx") 
    modelSubmission=reader.dfs['Q1']
    submission=marker.findGroups( modelSubmission )
    submission=marker.markUnspecifiedPositions(submission)
    assert( list( submission['IsCorrectCode?'] ) ==  ['Correct', 'Correct', 'Correct', 'Overcoded', 'Correct', 'Correct', 'Correct', 'Correct', 'Correct', 'Correct', 'Correct', 'Correct', 'Correct'])

    marker=calculateMark.Marker()
    reader=xls2dict.Reader("tests/modelAnswer.xlsx", isSubmission=False) 
    modelAnswer=reader.dfs['Q1']
    marker.prepareAnswer( modelAnswer )
    reader=xls2dict.Reader("tests/testSubmission.xlsx") 
    modelSubmission=reader.dfs['Q1']
    submission=marker.findGroups( modelSubmission )
    submission=marker.markUnspecifiedPositions(submission)
    assert( list( submission['IsCorrectCode?'] ) ==  ['Correct', 'Correct', 'Correct', 'Overcoded', 'Correct', 'Correct', 'Correct', 'Correct', 'Correct', 'Correct', 'Correct', 'Correct', 'Correct'])

def test_markPrefix():
    marker=calculateMark.Marker()
    reader=xls2dict.Reader("tests/modelAnswer.xlsx", isSubmission=False) 
    modelAnswer=reader.dfs['Q1']
    marker.prepareAnswer( modelAnswer )
    reader=xls2dict.Reader("tests/testSubmission.xlsx") 
    modelSubmission=reader.dfs['Q1']
    submission=marker.findGroups( modelSubmission )
    submission=marker.markPrefix(submission)
    assert( submission.submission.to_json() == """{
    "Code": {
        "0": "I25.11",
        "1": "I25.12",
        "10": "I48.9",
        "11": "E87.6",
        "12": "I10",
        "2": "I10",
        "3": "I31.0",
        "4": "T81.2",
        "5": "S25.0",
        "6": "Y60.0",
        "7": "Y92.22",
        "8": "J96.09",
        "9": "F17.1"
    },
    "Prefix?": {
        "0": "Correct",
        "1": "Correct",
        "10": "Correct",
        "11": "Correct",
        "12": "Correct",
        "2": "Correct",
        "3": "Not Correct",
        "4": "Correct",
        "5": "Correct",
        "6": "Correct",
        "7": "Correct",
        "8": "Correct",
        "9": "Correct"
    }
}""")    
    assert( list( submission.errorCodes ) == [u'P', None, u'B', None, u'A', u'A', u'A', u'A', None, u'L', None, u'L', None])

def test_markConvention():
    # test
    marker=calculateMark.Marker()
    reader=xls2dict.Reader("tests/modelAnswer.xlsx", isSubmission=False) 
    modelAnswer=reader.dfs['Q1']
    marker.prepareAnswer( modelAnswer )
    reader=xls2dict.Reader("tests/testSubmission.xlsx") 
    modelSubmission=reader.dfs['Q1']
    submission=marker.findGroups( modelSubmission )
    submission=marker.markConvention(submission)
    assert( list( submission.Grouping ) == [u'P', None, u'B', None, u'A', u'A', u'A', u'A', None, u'L', None, u'L', None])





if __name__ == "__main__":
    test_markUnspecifiedPositions()


