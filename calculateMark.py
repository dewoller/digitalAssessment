#!/usr/bin/python
# given 2 submissions, return the mark
# algorithm
# match specified positions
# match unspecified positions
# match intra group order
# match unordered groups
# match group order

# where wrong, put false in column for this label (where possible)  
# where correct, put true in column for this label
# put notes in notes regarding other false (along with marks)
# accumulate marks in marks variableS
# expects column names Grouping, Code

import sys, getopt
import pandas as pd
import numpy as np
import logging
import xls2dict
import re   
logger = logging.getLogger( __name__)

class Marker:

    def __init__(self):
        # model submission=4xN data frame containing columns:
        # Code, Grouping, IntragroupOrder, GroupOrder
        # special grouping - P - principal diagnosis (at start, more marks), L - last code
        # if no numbers in the intragrouporder column, codes can be in any order
        # if duplicate numbers in intragrouporder column, order don't care
        # algorithm
        # find groups and create groupStart array, groupOrder, groupMarking columns???
        # check intragroup order
        # check group order
        # TODO: sanity check model submission;  make sure valid columns exist, make sure everything is correct
        # rules - 
        # TODO: sanity check student submission;  make sure valid columns exist, make sure everything is correct
        self.notes=[]
        self.markCategory=[]
        self.marks=[]

    def prepareAnswer( self, answer):
        """ check answer for errors
        
        VALIDATION RULES
        contigious intragroup order, starting from 1
        all intragroup ordered groups must be fully specified
        groups P and L must be at first and last(s) positions respectively
        P group must have only 1 member, no intragroup order
        L group can never have intragroup order
        only 1 grouporder maximum per group
        columns should be labelled Code, Grouping, IntraGroupOrder, GroupOrder
        no duplicate codes
        
        ASSUMPTIONS
        No principal procedure
        0.5 marks for partial intragroup ordering
        """
        self.ma=answer
        self.ma.Code = [ re.sub( r" ", r"", x) for x in self.ma.Code ]
        self.maset = set(self.ma.Code)
        self.ma.Convention = [ re.sub( r" ", r"", x) for x in self.ma.Convention ]
        if 'Prefix' in self.ma.columns:
            self.ma.Prefix = [ re.sub( r" ", r"", x) for x in self.ma.Prefix ]

    def mark( self, submission):
        """ return a mark, and a marked up submission
        the latter ready to write back to excel file
        """

        """ did the student not submit anything with this name?"""
        if submission is None or len(submission)==0:
            return (pd.DataFrame(), 0)

        """ get rid of any rows without a code """
        submission = submission.loc[ np.where( notblank(submission['Code']) )[0]].reset_index(drop=True)
        submission.Code = [ re.sub( r" ", r"", x) for x in submission.Code ]

        # find the unique groups, to traverse later
        self.notes=[]
        self.markCategory=[]
        self.marks=[]

        # find and tag all the things that look like groups in the submission
        # a found group is a maximal length set of codes that are ALL in the model answer (with 1 possible mistake)
        # for example, def can be found in c_def_g, c_de_g, c_d_g, c_df_g
        submission = self.findGroups(submission)
        #print submission
        submission=self.markUnorderedGroups(submission)
        submission=self.markIntragroupOrder(submission)
        submission=self.markGroupOrder(submission)
        submission=self.markUnspecifiedPositions(submission)
        submission=self.markPrefix(submission)
        submission=self.markConvention(submission)

        for idx, mc in enumerate(self.markCategory):
            submission.ix[ idx, "Marks: Category" ] = mc

        totMarks = 0
        for idx, mark in enumerate(self.marks):
            submission.ix[ idx, "Marks: Amount" ] = mark
            totMarks = totMarks + mark

        for idx, note in enumerate(self.notes):
            submission.ix[ idx, "Marking Notes" ] = note

        submission.ix[ len(self.marks)+1, "Marks: Category" ] = ""
        submission.ix[ len(self.marks)+1, "Marks: Amount" ] = "------------"
        submission.ix[ len(self.marks)+2, "Marks: Category" ] = "Total"
        submission.ix[ len(self.marks)+2, "Marks: Amount" ] = totMarks
        
        return (submission, totMarks)

    def findGroups(self, submission):
        answerGroups=self.ma.Grouping[ notblank( self.ma.Grouping ) ].unique()
        submission.ix[:, 'Grouping'] = ""
        submission.ix[:, 'Grouping'] = None
        for group in answerGroups:
           submission = self.markGroup( submission, group, self.ma.Code[self.ma.Grouping==group] )
        return submission

    def markGroup( self, submission, groupID, search):
        # try to find group length len(codes)..2, from start to finish
        # traverse student submission one by one, see if enough codes exists, stop when found
        foundSlice = self.findSlice(submission.Code, search)
        if len(foundSlice ) != 0:
            # we have found a group, mark it in the submission
            submission.ix[ foundSlice.index, 'Grouping' ] = groupID
        return submission

    def findSlice( self, subCodes, search):
        """# subcodes - all the student submission codes
        # search - the model answer group slice we are searching for in subcodes
        # find the maximum length set of codes in search which match codes in student answer
        # try to find some group in subCodes, of length len(codes)..2
        #
        # the most important thing is to match the longest length of search
        # so, we first look for an exact match of search, and then,
        # look for for an exact match of search with 1 extra code interspersed
        # start looking for chunk one longer than searchSetLength, cause can have 1 mistake
        #
        # traverse student subCodes one by one, see if enough codes exists, stop when found
        # find the maximimum lenght winner from subCodes
        # either, exact winner, or winner with a single inner wrong element 
        # be satisfied with increasingly smaller sets of the model answer group
        """
        searchSet=set(search)
        for searchSliceLen in range(len(search), 0, -1):
            # go through the student answer, from start to end
            for startPos in range(0, len(subCodes) - searchSliceLen + 1 ): 
                # first, look for a contigious match
                # see if the current slice is an exact winner, that is, a set of codes in subCodes that 
                # has searchSliceLen of the codes in search
                # subcodes = abcdef, search = abc, ssl = 3
                # every code in this chunk of the student's submission 
                # has a match in the model answer (search)
                # and there is no bigger match 
                subSlice = subCodes.ix[ startPos:startPos + searchSliceLen - 1 ]
                #print "exact", searchSliceLen, startPos, len(subCodes), len(subSlice)
                if  (len(searchSet & set( subSlice )) == searchSliceLen) :
                    return subSlice
#
                # Now, if we are not already at the end, 
                # search for the single mistakes
                # if the first and last codes on the students answer match
                # and there is 1 mistake in the middle somethere
                if startPos + searchSliceLen - 1 == len(subCodes):
                    continue 
                subSlice = subCodes.ix[ startPos:startPos + searchSliceLen ]
                #print "inexact", searchSliceLen, startPos, len(subCodes), len(subSlice)
                if (subSlice.iloc[0] in searchSet   and
                    subSlice.iloc[ len(subSlice) - 1 ] in searchSet and 
                    len(searchSet & set( subSlice )) == searchSliceLen 
                    ):
                    #print "off by one"
                    #off by one winner
                    #Assert: there should be one incorrect code, in the middle of the group somewhere
                    #assert(len(temp)==len(foundSlice)-1, "should have one error code at this stage, "+temp+foundSlice)
                    return subSlice[ subSlice.isin(searchSet)]
        return []



    def markPrefix(self,submission):
        """ for each code in submission, mark if it has correct prefix """
        label='Prefix?'
        submission.loc[:,label]="Not Correct"
        if not 'Prefix' in submission.columns:
            return submission
        prefixes = submission.ix[:,("Code","Prefix")]
        prefixes.columns = [ "Code","subPrefix"]
        if len( prefixes ) == 0:
            return submission
        prefixes = prefixes.merge(self.ma.loc[:, ("Code","Prefix")], how="left", on="Code")
        isCorrect = list(not pd.isnull( c ) and c==s for s,c in zip(prefixes.subPrefix, prefixes.Prefix))
        submission.ix[ isCorrect, label ] = "Correct"
        nCorrect = sum( isCorrect )
        
        self.addNote("You had %d correct prefixes, gaining %2.1f marks" %(nCorrect, nCorrect * 0.5))
        self.addMark("%d Correct prefixes" % nCorrect, nCorrect * 0.5)

        return submission


    def markConvention(self,submission):

        """ for each code in submission, mark if it has correct convention """
        label='Convention?'
        submission.loc[:,label]="Not Correct"
        if not 'Convention' in submission.columns:
            return submission
        conventions = submission.ix[:,("Code","Convention")] 
        conventions.columns = ["Code","subConvention"]
        if len( conventions ) == 0:
            return submission
        conventions = conventions.merge(self.ma.loc[:, ("Code","Convention")], how="left", on="Code")

        """ it exists, and conventions match"""
        isCorrect =  list(not pd.isnull( c ) and 
                bool(re.match( c,s )) for c,s in zip(conventions.Convention, conventions.subConvention))
        submission.loc[ isCorrect, label ] = "Correct"
        nCorrect = sum( isCorrect )
        
        self.addNote("You had %d correct conventions, gaining %2.1f marks" %(nCorrect, nCorrect * 0.5))
        self.addMark("%d Correct conventions" % nCorrect, nCorrect * 0.5)


        return submission


    def markUnspecifiedPositions(self,submission):
        sset = set(submission.Code)
        nCorrect = len( sset & self.maset)
        self.addNote("You had %d correct codes, gaining %2.1f marks" %(nCorrect, nCorrect * 1))
        self.addMark("%d Correct Codes" % nCorrect, nCorrect * 1)
        noverCode = len( sset.difference(self.maset) )
        label='IsCorrectCode?'
        submission.loc[:,label]="Overcoded"
        submission.loc[ submission.Code.isin( self.maset ),label]="Correct"

        if noverCode>0:
            self.addNote("You had %d overcodes" %(noverCode))
            #self.addNote("You had %d overcodes, losing %2.1f marks" %(noverCode, noverCode * 0.5))
            #self.addMark("%d Overcodes" % noverCode, noverCode * -0.5)

        return submission

    def markIntragroupOrder(self,submission):
        """
        for each answer group
        compare answer group members to the submission group. (length of intersection)
        for each member of answer group, in order, make sure that the current one
        is after the last one
        .5 marks for each common member
        .5 marks if all the submission members are in the correct order, according to the answer group
        """
        label='OrderedGroups'
        submission.loc[:,label]=None

        # it has a Grouping and an intraGroupOrder
        maGroups= self.ma[ eAnd( notblank(self.ma.IntraGroupOrder), notblank(self.ma.Grouping)) ].Grouping.unique()
        for group in maGroups:
            # take the group slice
            magSlice = self.ma[ self.ma.Grouping==group].Code
            subSlice = submission[ submission.Grouping==group].Code
            submission.loc[ submission.Code.isin( set(magSlice) ), label] = group
            if len( subSlice ) == 0:
                self.addNote( "Entirely missing Ordered Group %s, should be %s " % (group, pprintSlice(magSlice)) )
                next
            currentPos = -1
            stillCorrect=True
            for code in subSlice:

                # what order should this code be in
                position=self.ma.loc[ self.ma[ self.ma.Code == code ].index,:].IntraGroupOrder
                position=position[position.index[0]]

                # we went backwards!
                if position<currentPos:
                    self.addNote("Ordered Group %s, incorrect order, answer=%s, you had %s" 
                            % (group, pprintSlice(magSlice), pprintSlice(subSlice)))
                    stillCorrect=False
                    break
                else:
                    currentPos = position

            if stillCorrect:
                if len( subSlice ) > 1:
                    self.addNote( "Ordered Group %s, answer is %s, completely correct order, 0.5 marks" 
                            % (group, pprintSlice(magSlice)) )
                    self.addMark("Ordered Group %s" % group, 0.5)
                else:
                    self.addNote( "Ordered Group %s, answer is %s, you only had %s, too short" % (group, pprintSlice(magSlice), pprintSlice(subSlice)) )


        return submission

    def markUnorderedGroups(self,submission):
        """ single interruption ok
        # any group larger than size 1 ok    
        

        Algorithm
        # for each unorderedGroup (ie, no intragroup order )
            # for each slice S of size length(uog) , 
            # if uog - S = null set, we have a winner.  Mark group correct
        """
        label='UnorderedGroups'
        maGroups= self.ma[ eAnd( isblank(self.ma.IntraGroupOrder),  notblank(self.ma.Grouping)) ].Grouping.unique()

        # P and L groups are taken care of by absoluteOrdering routine.  Different marks too
        #maGroups = set(maGroups).difference( set("P", "L"))
        submission.loc[:,label]=None
        for group in maGroups:
            # take the group slice
            magSet = set( self.ma[ self.ma.Grouping==group].Code)
#            import pdb;pdb.set_trace()
            subSlice = submission[ submission.Grouping==group].Code
            subSet = set( subSlice )
            nCorrect=len( magSet & subSet )
            submission.loc[ submission.Code.isin( magSet ), label] = group
            if group=="P":
                if nCorrect == len(magSet ) : # all correct, principal
                    self.addNote( "Correct principal diagnosis, 1 mark"  )
                    self.addMark("Principal Diagnosis", 1)
                else:
                    self.addNote( "Incorrect principal diagnosis, answer is %s, you had %s " % ( pprintSlice(magSet), pprintSlice(subSet)) )
                next

            if group=="L" : # Last Codes 
                if len(subSlice) > 0 and max( subSlice.index )  == max(submission.index ):
                    self.addNote( "Correct final codes, 0.5 marks"  )
                    self.addMark( "Final Code(s) Group", 0.5 )
                else:
                    self.addNote( "Incorrect final code(s), should be %s" % ( pprintSlice(magSet)) )

            # we don't need to process the group if it is only 1 code
            if len( magSet ) == 1:
                next



            if nCorrect == len(magSet ) : # all correct
                self.addNote( "Unordered Group %s, %s entirely correct, 0.5 marks" % (group, pprintSlice(magSet)) )
                self.addMark("Unordered Group %s" % group, 0.5)
            elif (nCorrect > 0 ) :
                self.addNote( "Unordered Group %s partially correct, answer is %s, you had %s, 0.5 marks " 
                        % (group, pprintSlice(magSet), pprintSlice(subSet)) )
                self.addMark("Unordered Group %s" % group, 0.5)
            else:
                self.addNote( "Unordered Group %s, %s entirely missing" % (group, pprintSlice(magSet)) )

        return submission

    def markGroupOrder(self,submission):
        """ for each non null GroupOrder, find out the group 
        for each group, make sure the subSlice for this group is consecutive
        """

        """ make sure that there exist groupOrders in the answer"""
        groupOrder = self.ma.ix[ notblank(self.ma.GroupOrder),("Grouping","GroupOrder")]
        if len( groupOrder ) == 0:
            return submission

        """ find out where these groups live in the submission:
            create data frame with rows Grouping, GroupOrder, and mindex, maxdex 
            1) find all the rows that relate to the answer grouping, and their minimum and maximum index (mindex)
        """
        submissionGroupPos = submission[ submission.Grouping.isin(groupOrder.Grouping)]
        submissionGroupPos.loc[:,"index"]=submissionGroupPos.index
        submissionGroupPosMin = pd.DataFrame(submissionGroupPos.groupby("Grouping")["index"].agg(np.min))
        submissionGroupPosMin["mindex"] = submissionGroupPosMin["index"]
        submissionGroupPosMax = pd.DataFrame(submissionGroupPos.groupby("Grouping")["index"].agg(np.max))
        submissionGroupPosMax["maxdex"] = submissionGroupPosMax["index"]

        # error check to make sure we have got Min and Max Grouping columns
        if not 'Grouping' in submissionGroupPosMin.columns:
            submissionGroupPosMin['Grouping'] = submissionGroupPosMin.index
        if not 'Grouping' in submissionGroupPosMax.columns:
            submissionGroupPosMax['Grouping']=submissionGroupPosMax.index
        groupOrder=groupOrder.merge(submissionGroupPosMin, how='left', on="Grouping")
        groupOrder=groupOrder.merge(submissionGroupPosMax, how='left', on="Grouping").sort(columns="mindex")

        
        groupOrder.loc[ : , "Consecutive"] = False
        i=0
        for go in groupOrder.GroupOrder:
            if str(go).endswith("N"):
                groupOrder.loc[ i, "Consecutive"] = True
                groupOrder.loc[ i, "GroupOrder"] = groupOrder.loc[ i, "GroupOrder"][0:-1] 
            i = i + 1


        """ go through each group in mindex order, make sure that 
         - all the groups exist
         -  the groups are consecutive (when the first group ends in an N, and 
         -  the GroupOrder ascends

        """
        if ( 
                all( not np.isnan( i ) for i in groupOrder.ix[:, "mindex"] )
                and all( not groupOrder.ix[i,"Consecutive"] 
                         or groupOrder.ix[i, "maxdex"]+1 == groupOrder.ix[i+1, "mindex"]
                            for i in xrange( len(groupOrder) -1 )
                       )

                and all( groupOrder.ix[i, "GroupOrder"] <= groupOrder.ix[i+1, "GroupOrder"]  
                         for i in xrange( len(groupOrder) -1 )
                        )
             ):
            self.addNote( "Correct ALL group ordering, 0.5 marks"  )
            self.addMark("All Groups Ordering", 0.5)
        else:
            self.addNote( "Incorrect ALL group ordering"  )

        return submission

    def addNote(self, text ):
        self.notes.append( text )

    def addMark(self, markCategory, marks ):
        self.markCategory.append( markCategory )
        self.marks.append( marks )


def pprintSlice(slice):
    return "[" + (",".join(slice)) + "]"

""" notnull replacement.  Assumes each cell is a string """
def notblank(s):
  return [ len(x)>0 for x in s]  

""" isnull replacement.  Assumes each cell is a string """
def isblank(s):
  return [ len(x)==0 for x in s]  

def eAnd( list_a, list_b ):
    return [ x&y for (x,y) in zip(list_a, list_b)]


def usage():
    print """ Usage: %s 
    h=help
    f file = file to parse
    """ % (sys.argv[0])

def main(argv):
    import xls2dict, calculateMark
    import pandas as pd
    reader=xls2dict.Reader("tests/modelAnswer.xlsx") 
    submission=xls2dict.Reader("tests/testSubmission.xlsx") 
    sheet="Q1"
    modelAnswer=reader.dfs[ sheet ]
    testSubmission=submission.dfs[ sheet ]
    marker=calculateMark.Marker()
    marker.prepareAnswer(modelAnswer)
    print marker.mark(testSubmission)
    return
    print marker.findSlice( pd.Series(["a","b", "c", "d", "e", "f", "g"]), pd.Series(["d",'f', 'g']))
    print marker.findSlice( pd.Series(["a","b", "c", "d", "e", "f", "g"]), pd.Series(["f",'d', 'g']))

    print marker.findSlice( pd.Series(["a","b", "c", "d", "e", "f", "g"]), pd.Series(["a", 'c']))
    print marker.findSlice( pd.Series(["a","b", "c", "d", "e", "f", "g"]), pd.Series(["c", 'e']))
    print marker.findSlice( pd.Series(["a","b", "c", "d", "e", "f", "g"]), pd.Series(["e", 'g']))
    print marker.findSlice( pd.Series(["a","b", "c", "d", "e", "f", "g"]), pd.Series(["a", "b", 'd']))
    print marker.findSlice( pd.Series(["a","b", "c", "d", "e", "f", "g"]), pd.Series(["a", "c", 'd']))
    print marker.findSlice( pd.Series(["a","b", "c", "d", "e", "f", "g"]), pd.Series(["a","b", "c", "d", "e", "f", "g"]))
    print marker.findSlice( pd.Series(["a","b", "c", "d", "e", "f", "g"]), pd.Series(["a","b", "c", "d", "e", "g"]))
    print marker.findSlice( pd.Series(["a","b", "c", "d", "e", "f", "g"]), pd.Series(["a","b", "c", "d", "e", "f"]))
    print marker.findSlice( pd.Series(["a","b", "c", "d", "e", "f", "g"]), pd.Series(["a", "c", "d", "e", "f", "g"]))
    print marker.findSlice( pd.Series(["a","b", "c", "d", "e", "f", "g"]), pd.Series(["b", "c", "d", "e", "f", "g"]))
    print marker.findSlice( pd.Series(["a","b", "c", "d", "e", "f", "g"]), pd.Series(["Z", "c", "d", "e", "f", "g"]))
    print marker.findSlice( pd.Series(["a","b", "c", "d", "e", "f", "g"]), pd.Series(["a", "a", 'a']))
    print marker.findSlice( pd.Series(['a', 'b', 'c']), pd.Series(["a", "b","c"]))
    print marker.findSlice( pd.Series(["Z", 'a', 'b', 'c', 'd']), pd.Series(["a", "b","c"]))
    print marker.findSlice( pd.Series(["a","b", "c", "d", "e", "f", "g"]), pd.Series(["a","b"]))
    print marker.findSlice( pd.Series(["a","b", "c", "d", "e", "f", "g"]), pd.Series(["a"]))
    print marker.findSlice( pd.Series(["a","b", "c", "d", "e", "f", "g"]), pd.Series(["b"]))
    print marker.findSlice( pd.Series(["a","b", "c", "d", "e", "f", "g"]), pd.Series(["c"]))
    

if __name__ == "__main__":
    main(sys.argv[1:])

    

