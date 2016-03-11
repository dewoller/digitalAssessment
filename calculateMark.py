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
        # TODO: sanity check model submission;  make sure valid columns exist, make sure everything is correct
        # rules - 
        # TODO: sanity check student submission;  make sure valid columns exist, make sure everything is correct
        self.errorColumns = ["Code", "AOI", "Value", "ValueSubmitted", "IsCorrect"]
        self.initalizeSubmissionDetails()

    def initalizeSubmissionDetails(self):
        self.notes=[]
        self.markCategory=[]
        self.marks=[]
        self.errorFrame = pd.DataFrame(columns=self.errorColumns)

    def prepareAnswer( self, answer):
        """
        # model submission=4xN data frame containing columns:
        # Code, Grouping, IntragroupOrder, GroupOrder
        # special grouping - P - principal diagnosis (at start, more marks), L - last code
        # if no numbers in the intragrouporder column, codes can be in any order
        # if duplicate numbers in intragrouporder column, order don't care
        """
        self.errorCheckMaster(answer)
        self.ma=self.dataClean( answer )

    def errorCheckMaster( self, answer):
        """ check answer for errors
        
        VALIDATION RULES
        proper columns
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
        self.errorCheckSubmission( answer ) 
        for colName in ["Grouping", "IntraGroupOrder", "GroupOrder"]:
            assert colName in answer.columns, "We need a %s column in the master spreadsheet" % colName

    def errorCheckSubmission( self, answer):
        """ check answer for errors
        
        VALIDATION RULES
        proper columns
        
        """
        
        for colName in ["Code", "Convention", "GroupOrder"]:
            assert colName in answer.columns, "We need a %s column in the master spreadsheet" % colName

    """ standard data cleaning of an answer set.  
    """
    def dataClean( self, answer ):

        """ get rid of any rows without a code """
        answer = answer.loc[ np.where( notblank(answer['Code']) )[0]].reset_index(drop=True) # pylint: disable=E1101

        """ get rid of any spaces """
        answer.Code = [ re.sub( r" ", r"", x) for x in answer.Code ]
        answer.Convention = [ re.sub( r" ", r"", x) for x in answer.Convention ]
        if 'Prefix' in answer.columns:
            answer.Prefix = [ re.sub( r" ", r"", x) for x in answer.Prefix ]
        return answer

    def mark( self, submission):
        """ return a mark, and a marked up submission
        the latter ready to write back to excel file
        # algorithm
        # find groups and create groupStart array, groupOrder, groupMarking columns???
        # check intragroup order
        # check group order
        """

        """ did the student not submit anything with this name?"""
        if submission is None or len(submission)==0:
            submission = pd.DataFrame( columns = self.ma.columns)
            #return (pd.DataFrame(), 0, pd.DataFrame())

        submission = self.dataClean( submission ) 
        self.initalizeSubmissionDetails()

        submission = self.findGroups(submission)
        submission=self.markUnspecifiedPositions(submission)

        if notblank( self.ma.Grouping ) != []:
            submission=self.markUnorderedGroups(submission)
            submission=self.markIntragroupOrder(submission)
            submission=self.markGroupOrder(submission)
            submission=self.markPrefix(submission)
            submission=self.markConvention(submission)

        label = "Marks: Category" 
        submission = self.addColumn( submission, label )
        for idx, mc in enumerate(self.markCategory):
            submission.loc[ idx, label ] = mc

        totMarks = 0
        label = "Marks: Amount" 
        submission = self.addColumn(submission, label )
        for idx, mark in enumerate(self.marks):
            submission.loc[ idx, label ] = mark
            totMarks = totMarks + mark

        label = "Marking Notes" 
        submission = self.addColumn(submission, label )
        for idx, note in enumerate(self.notes):
            submission.loc[ idx, label ] = note

        submission.loc[ len(self.marks)+1, "Marks: Category" ] = ""
        submission.loc[ len(self.marks)+1, "Marks: Amount" ] = "------------"
        submission.loc[ len(self.marks)+2, "Marks: Category" ] = "Total"
        submission.loc[ len(self.marks)+2, "Marks: Amount" ] = totMarks
        
        return (submission, totMarks, self.errorFrame)

    """ 
        # find and tag all the things that look like groups in the submission
        # a found group is a maximal length set of codes that are ALL in the model answer (with 1 possible mistake)
        # for example, def can be found in c_def_g, c_de_g, c_d_g, c_df_g
    """
    def findGroups(self, submission):
        answerGroups=self.ma.Grouping[ notblank( self.ma.Grouping ) ].unique()
        label = "Grouping" 
        submission = self.addColumn( submission, label )
        submission.ix[:, label ] = ""
        submission.ix[:, label ] = None
        for group in answerGroups:
           submission = self.markGroup( submission, group, self.ma.Code[self.ma.Grouping==group] )
        return submission

    """"
        # try to find group length len(codes)..2, from start to finish
        # traverse student submission one by one, see if enough codes exists, stop when found
    """
    def markGroup( self, submission, groupID, search):
        foundSlice = self.findSlice(submission.Code, search)
        if len(foundSlice ) != 0:
            # we have found a group, mark it in the submission
            submission.ix[ foundSlice.index, 'Grouping' ] = groupID
        return submission

    def findSlice( self, subCodes, search):
        """# subcodes - all the student submission codes
        # search - the model answer group slice we are searching for in subcodes
        # find the maximum length set of codes in search which match somewhere in the student subCodes
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
        """ for each code in submission, mark if it has correct prefix 
            assume all submissions are incorrect, mark those that are correct 
        """
        label='Prefix?'
        submission = self.addColumn( submission, label )
        submission.loc[:,label]="Not Correct"
        if not 'Prefix' in submission.columns:
            return submission
        prefixes = submission.ix[:,("Code","Prefix")]
        prefixes.columns = [ "Code","submissionPrefix"]
        if len( prefixes ) == 0:
            return submission
        prefixes = prefixes.merge(self.ma.loc[:, ("Code","Prefix")], how="left", on="Code")
        isCorrect = list(not pd.isnull( c ) and c==s for s,c in zip(prefixes.submissionPrefix, prefixes.Prefix))
        submission.ix[ isCorrect, label ] = "Correct"
        nCorrect = sum( isCorrect )
        
        """ 
        prepare errorframe from a 'what is correct' perspective
        1) create error dataframe from master, columns Code and prefix
        1a) rename prefix to Value
        2) fill submission prefix, matching by code
        3) fill IsCorrect
        """
        errors = self.ma.ix[:,("Code","Prefix")]
        errors.columns = [ "Code", "Value" ]
        errors = errors.merge(submission.loc[:, ("Code","Prefix")], how="left", on="Code")
        errors.columns = [ "Code", "Value", "ValueSubmitted" ]
        errors = self.addColumn( errors, "AOI" )
        errors.loc[:,"AOI"]="Prefix"
        label = "IsCorrect"
        errors = self.addColumn( errors, label )
        errors.loc[:, label ]="False"
        isCorrect = list(not pd.isnull( c ) and c==s 
                for s,c in zip(errors.Value, errors.ValueSubmitted))
        errors.ix[ isCorrect, label ] = "True"
        self.addError(  errors )

        self.addNote("You had %d correct prefixes, gaining %2.1f marks" %(nCorrect, nCorrect * 0.5))
        self.addMark("%d Correct prefixes" % nCorrect, nCorrect * 0.5)

        return submission

    """ 
    add list of errors to the global errorframe
    expects columns:
        Code
        AOI
        IsCorrect

        Value
        ValueSubmitted

        ActionType should be one of:
            Code
            Prefix
            Convention
            Grouping
            OrderedGroup
            Primary
            Last
        XX    MissingCode
            Overcoded
            SubstituteCode
        

    """
    def addError( self, thisErrorFrame ):
        if isinstance(thisErrorFrame, dict):
            self.errorFrame = self.errorFrame.append(thisErrorFrame, ignore_index=True )
        else:
            self.errorFrame = self.errorFrame.append(thisErrorFrame )

    def markConvention(self,submission):

        """ for each code in submission, mark if it has correct convention """
        label='Convention?'
        submission = self.addColumn( submission, label )
        submission.loc[:,label]="Not Correct"
        if not 'Convention' in submission.columns:
            return submission
        conventions = submission.ix[:,("Code","Convention")] 
        conventions.columns = ["Code","submissionConvention"]
        if len( conventions ) == 0:
            return submission
        conventions = conventions.merge(self.ma.loc[:, ("Code","Convention")], how="left", on="Code")

        """ it exists, and conventions match"""
        isCorrect =  list(not pd.isnull( c ) and 
                bool(re.match( c,s )) for c,s in zip(conventions.Convention, conventions.submissionConvention))
        submission.loc[ isCorrect, label ] = "Correct"
        nCorrect = sum( isCorrect )
        
        """ 
        prepare errorframe 
        """
        errors = self.ma.ix[:,("Code","Convention")]
        errors.columns = [ "Code", "Value" ]
        errors = errors.merge(submission.loc[:, ("Code","Convention")], how="left", on="Code")
        errors.columns = [ "Code", "Value", "ValueSubmitted" ]
        errors = self.addColumn( errors, "AOI" )
        errors.loc[:,"AOI"]="Convention"
        label = "IsCorrect"
        errors = self.addColumn( errors, label )
        errors.loc[:, label ]="False"
        isCorrect = list(not pd.isnull( c ) and  bool(re.match( c,s ))
                for s,c in zip(errors.Value, errors.ValueSubmitted))
        errors.ix[ isCorrect,  label ] = "True"
        self.addError(  errors )

        self.addNote("You had %d correct conventions, gaining %2.1f marks" %(nCorrect, nCorrect * 1))
        self.addMark("%d Correct conventions" % nCorrect, nCorrect *  1)


        return submission

    def addColumn( self, submission, label) : 
        return pd.concat([submission, pd.DataFrame(columns=[ label ])])

    def markUnspecifiedPositions(self,submission):
        sset = set(submission.Code)
        maset = set(self.ma.Code)
        nCorrect = len( sset & maset)
        self.addNote("You had %d correct codes, gaining %2.1f marks" %(nCorrect, nCorrect * 1))
        self.addMark("%d Correct Codes" % nCorrect, nCorrect * 1)
        noverCode = len( sset.difference(maset) )
        label='IsCorrectCode?'
        submission = self.addColumn(submission, label )
        submission.loc[:,label]="Overcoded"
        submission.loc[ submission.Code.isin( maset ),label]="Correct"


        """ 
        prepare errorframe  - 1) Correct and incorrect master codes
        if we have any master codes in this sheet, do it!
        """
        if len(self.ma.index) > 0:
            errors = self.ma.ix[:,("Code","Code", "Code")]
            errors.columns = [ "Code", "Value", "ValueSubmitted" ]
            errors = self.addColumn( errors, "AOI" )
            errors.loc[:,"AOI"]="Codes"
            label = "IsCorrect"
            errors = self.addColumn( errors, label )
            errors.loc[:, label ]="False"

            isCorrect = errors.Code.isin( submission.Code ) 
            errors.ix[ isCorrect, label ] = "True"
            errors.ix[ ~ isCorrect, "ValueSubmitted" ] = ""

            self.addError(  errors )

        """ 
        prepare errorframe  - 2) Overcodes
        get submitted codes not in master
        """
        errors = pd.DataFrame(submission.ix[ ~submission.Code.isin( self.ma.Code ),("Code")])
        if len( errors.index ) > 0: 
            errors.columns=["ValueSubmitted"]
            errors = self.addColumn( errors, "AOI" )
            errors.loc[:,"AOI"]="Overcode"
            label = "IsCorrect"
            errors = self.addColumn( errors, label )
            errors.loc[:, label ]="False"
            errors = self.addColumn( errors, "Code" )
            errors = self.addColumn( errors, "Value" )

            self.addError( errors )

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
        """
        label='OrderedGroups'
        submission = self.addColumn(submission, label )
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
                self.addError( {
                    'AOI': 'IntraGroupOrder', 
                    'Value': pprintSlice(magSlice), 
                    'ValueSubmitted': "",
                    'Code': "", 
                    'IsCorrect': "False" 
                    })
                next
            currentPos = -1
            stillCorrect=True
            for code in subSlice:

                # what order should this code be in
                thisCodeIntraGroupOrder=self.ma.loc[ self.ma[ self.ma.Code == code ].index,:].IntraGroupOrder
                thisCodeDesiredposition=float( thisCodeIntraGroupOrder[thisCodeIntraGroupOrder.index[0]])

                # we went backwards!
                if thisCodeDesiredposition < currentPos:
                    self.addNote("Ordered Group %s, incorrect order, answer=%s, you had %s" 
                            % (group, pprintSlice(magSlice), pprintSlice(subSlice)))
                    self.addError( {
                        'AOI': 'IntraGroupOrder', 
                        'Value': pprintSlice(magSlice), 
                        'ValueSubmitted': pprintSlice( subSlice ),
                        'Code': "", 
                        'IsCorrect': "False" 
                        })
                    stillCorrect=False
                    break
                else:
                    currentPos = thisCodeDesiredposition

            if stillCorrect:
                if len( subSlice ) > 1:
                    self.addNote( "Ordered Group %s, answer is %s, completely correct order, 0.5 marks" 
                            % (group, pprintSlice(magSlice)) )
                    self.addMark("Ordered Group %s" % group, 0.5)
                    self.addError( {
                        'AOI': 'IntraGroupOrder', 
                        'Value': pprintSlice(magSlice), 
                        'ValueSubmitted': pprintSlice( subSlice ),
                        'Code': "", 
                        'IsCorrect': "True" 
                        })
                else:
                    self.addNote( "Ordered Group %s, answer is %s, you only had %s, a single code is not enough for a group" % (group, pprintSlice(magSlice), pprintSlice(subSlice)) )
                    self.addError( {
                        'AOI': 'IntraGroupOrder', 
                        'Value': pprintSlice(magSlice), 
                        'ValueSubmitted': pprintSlice( subSlice ),
                        'Code': "", 
                        'IsCorrect': "False" 
                        })

        return submission

    def markUnorderedGroups(self,submission):
        """ single interruption ok
        # any group larger than size 1 ok    
        

        Algorithm
        # for each unorderedGroup (ie, no intragroup order )
            # for each slice S of size length(uog) , 
            # if uog - S = null set, we have a winner.  Mark group correct
        """

        maGroups= self.ma[ eAnd( isblank(self.ma.IntraGroupOrder),  notblank(self.ma.Grouping)) ].Grouping.unique()

        # P and L groups are taken care of by absoluteOrdering routine.  Different marks too
        #maGroups = set(maGroups).difference( set("P", "L"))
        label='UnorderedGroups'
        submission = self.addColumn(submission, label )
        submission.loc[:,label]=None
        for group in maGroups:
            # take the group slice
            magSet = set( self.ma[ self.ma.Grouping==group].Code)
            subSlice = submission[ submission.Grouping==group].Code
            subSet = set( subSlice )
            nCorrect=len( magSet & subSet )
            submission.loc[ submission.Code.isin( magSet ), label] = group
            if group=="P":
                if nCorrect == len(magSet ) : # all correct, principal
                    self.addNote( "Correct principal diagnosis, 1 mark"  )
                    self.addMark("Principal Diagnosis", 1)
                    self.addError( {
                        'AOI': 'PrincipalCode', 
                        'Value': pprintSlice(magSet), 
                        'ValueSubmitted': pprintSlice( subSet ),
                        'Code': "", 
                        'IsCorrect': "True" 
                        })
                else:
                    self.addNote( "Incorrect principal diagnosis, answer is %s, you had %s " % ( pprintSlice(magSet), pprintSlice(subSet)) )
                    self.addError( {
                        'AOI': 'PrincipalCode', 
                        'Value': pprintSlice(magSet), 
                        'ValueSubmitted': pprintSlice( subSet ),
                        'Code': "", 
                        'IsCorrect': "False" 
                        })
                next

            if group=="L" : # Last Codes 
                if len(subSlice) > 0 and max( subSlice.index )  == max(submission.index ):
                    self.addNote( "Correct final codes, 0.5 marks"  )
                    self.addMark( "Final Code(s) Group", 0.5 )
                    self.addError( {
                        'AOI': 'LastCode', 
                        'Value': pprintSlice(magSet), 
                        'ValueSubmitted': pprintSlice( subSet ),
                        'Code': "", 
                        'IsCorrect': "True" 
                        })
                else:
                    self.addNote( "Incorrect final code(s), should be %s" % ( pprintSlice(magSet)) )
                    self.addError( { 'AOI': 'LastCode', 
                        'Code': "", 
                        'IsCorrect': "False" ,
                        'Value': pprintSlice(magSet), 
                        'ValueSubmitted': pprintSlice( subSet ),
                        })

            # we don't need to process the group if the master says it is only one code long
            if len( magSet ) == 1:
                next



            if nCorrect == len(magSet ) : # all correct
                self.addNote( "Unordered Group %s, %s entirely correct, 0.5 marks" % (group, pprintSlice(magSet)) )
                self.addMark("Unordered Group %s" % group, 0.5)
                self.addError( { 'AOI': 'UnorderedGroup', 
                    'Code': "", 
                    'IsCorrect': "True" ,
                    'Value': pprintSlice(magSet), 
                    'ValueSubmitted': pprintSlice( subSet ),
                    })
            elif (nCorrect > 0 ) :
                self.addNote( "Unordered Group %s partially correct, answer is %s, you had %s, 0.5 marks " 
                        % (group, pprintSlice(magSet), pprintSlice(subSet)) )
                self.addMark("Unordered Group %s" % group, 0.5)
                self.addError( { 'AOI': 'UnorderedGroup', 
                    'Code': "", 
                    'IsCorrect': "False" ,
                    'Value': pprintSlice(magSet), 
                    'ValueSubmitted': pprintSlice( subSet ),
                    })
            else:
                self.addNote( "Unordered Group %s, %s entirely missing" % (group, pprintSlice(magSet)) )
                self.addError( { 'AOI': 'UnorderedGroup', 
                    'Code': "", 
                    'IsCorrect': "False" ,
                    'Value': pprintSlice(magSet), 
                    'ValueSubmitted': "",
                    })

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
                all( not np.isnan( i ) for i in groupOrder.ix[:, "mindex"] ) # pylint: disable=E1101  
                and all( not groupOrder.ix[i,"Consecutive"] 
                         or groupOrder.ix[i, "maxdex"]+1 == groupOrder.ix[i+1, "mindex"]
                            for i in range( len(groupOrder) -1 )
                       )

                and all( groupOrder.ix[i, "GroupOrder"] <= groupOrder.ix[i+1, "GroupOrder"]  
                         for i in range( len(groupOrder) -1 )
                        )
             ):
            self.addNote( "Correct ALL group ordering, 0.5 marks"  )
            self.addMark("All Groups Ordering", 0.5)
            self.addError( { 'AOI': 'AllGroupsOrdering', 
                'Code': "", 
                'IsCorrect': "True" ,
                'Value': "", 
                'ValueSubmitted': "",
                })

        else:
            self.addNote( "Incorrect ALL group ordering"  )
            self.addError( { 'AOI': 'AllGroupsOrdering', 
                'Code': "", 
                'IsCorrect': "False" ,
                'Value': "", 
                'ValueSubmitted': "",
                })


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
    print( """ Usage: %s 
    h=help
    f file = file to parse
    """ % (sys.argv[0]))

def main(argv):
    import xls2dict, calculateMark
    import pandas as pd
#    reader=xls2dict.Reader("tests/modelAnswer.xlsx") 
#    submission=xls2dict.Reader("tests/testSubmission.xlsx") 
#    sheet="Q1"
#    modelAnswer=reader.dfs[ sheet ]
#    testSubmission=submission.dfs[ sheet ]
    marker=calculateMark.Marker()
#    marker.prepareAnswer(modelAnswer)
#    print marker.mark(testSubmission)
    #return
    
    reader=xls2dict.Reader("tests/modelAnswer.xlsx", isSubmission=False) 
    modelAnswer=reader.dfs['Q1']
    marker.prepareAnswer( modelAnswer )
    reader1=xls2dict.Reader("tests/testSubmission.xlsx") 
    modelSubmission=reader1.dfs['Q1']
    #submission=marker.findGroups( modelSubmission )
    submission=marker.findGroups( modelSubmission )
    #print(list(submission.Grouping))
    submission=marker.markIntragroupOrder(submission)
    assert( list( submission.Grouping ) == [u'P', None, u'B', None, u'A', u'A', u'A', u'A', None, u'L', None, u'L', None])

if __name__ == "__main__":
    main(sys.argv[1:])

    

