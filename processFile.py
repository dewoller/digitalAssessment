import warnings
warnings.filterwarnings('error', ".*SettingWithCopyWarning.*")


import sys, getopt
import pandas as pd
pd.options.mode.chained_assignment=None
import zipfile
import tempfile
import logging
import xls2dict
import calculateMark
import os,re
import ntpath
LOGGER = logging.getLogger( __name__)
_debug=0
"""
process a single submission / excel file, given this answer and submission
stores results in results file (for return to student?)
returns the mark
"""
def processSubmission( answerFile, submissionFile, resultsFilePath):
    modelAnswerReader = xls2dict.Reader(answerFile, isSubmission=False) 
    submissionReader = xls2dict.Reader(submissionFile) 
    #resultsFilePath = submissionFile + ".results.xlsx"
    resultsWriter = pd.ExcelWriter(resultsFilePath)
    marker=calculateMark.Marker()
    perSheetMarks = {}
    perSheetErrors = {}
    errorFrame= pd.DataFrame()
    for sheet in sorted(modelAnswerReader.getSheetNames()):
        if _debug==1:
            print "%s" % sheet
        marker.prepareAnswer(modelAnswerReader.getSheet( sheet ))
        (resultSheet, marks, errorFrame) = marker.mark( submissionReader.getSheet( sheet ))
        resultSheet.to_excel(resultsWriter, sheet, index=False)
        perSheetMarks[ sheet ] = marks
        perSheetErrors[ sheet ] = errorFrame

    resultsWriter.save()
    return (perSheetMarks, perSheetErrors)


identityErrorColumns = ["class", "week", "student", "question", "sheet"]
""" 
processZip needs to add identity error columns into errorFrame
get question from folder
get class and week from path
get student from filename
get sheet from sheet? 

typical filename
#/home/dewoller/mydoc/research/digitalAssessment/submissions/S1_2015_CCC/wk1
"""

def processSubmissionZip( answerFile, submissionZip, outZip, errorFile = None ):
    showHeader=True
    id = {}
    for name in  identityErrorColumns:
        id[ name ] = ""
    match=re.search( ".*submissions/([^/]*)/([^/]*)/CMR_(\d*).*", answerFile )
    
    if match:
        id["class"]=match.group(1)
        id["week"]=match.group(2)
        id["question"]=match.group(3)

    tmpInDir = tempfile.mkdtemp()
    tmpOutDir = tempfile.mkdtemp()
    resultsFileName = "__Marks.xlsx"
    secondErrorFileName = "__Errors.csv"
    resultsFilePath =  tmpOutDir + os.path.sep + resultsFileName
    secondErrorFilePath =  tmpOutDir + os.path.sep + secondErrorFileName
    errorBuffers=[]
    marks={}
    zout = zipfile.ZipFile( outZip, "w")
    with zipfile.ZipFile(submissionZip, "r") as z:
        for name in z.namelist():
            z.extract( name, tmpInDir )
            baseName =ntpath.basename(name) 
            inFile = tmpInDir + os.path.sep + name
            match = re.search(tmpInDir + "/([^_]*).*", inFile)
            if match:
                id["student"]=match.group(1)
            if _debug==1:
                print "FILE=\n\"%s\"\n" % inFile 
            outFile= tmpOutDir + os.path.sep + baseName
            (marks[ baseName ], errorFrameAll) = processSubmission(answerFile, inFile, outFile)
            for id["sheet"], errorFrame in errorFrameAll.iteritems():
                if len(errorFrame.index) >0 :
                    for name in  identityErrorColumns:
                        errorFrame.loc[:, name ] = id[ name ]
                    errorBuffers.append(errorFrame.to_csv( index=False, header=showHeader))
                    showHeader=False
            zout.write(outFile, baseName)


    # process "perfect student"

    fd,perfectAnswerName = tempfile.mkstemp(".xlsx")
    (marks["Perfect"], errorFrameAll) = processSubmission( answerFile, answerFile, perfectAnswerName )
    os.close(fd)

    id["student"]="Perfect"
    for id["sheet"], errorFrame in errorFrameAll.iteritems():
        if len(errorFrame.index) >0 :
            for name in  identityErrorColumns:
                errorFrame.loc[:, name ] = id[ name ]
            errorBuffers.append(
                    errorFrame.to_csv( index=False, header=showHeader)
                    )

    # save results file, and error file
    marks2ExcelFile(marks, resultsFilePath)
    if errorFile:
      errors2CSV(errorBuffers, errorFile)

    errors2CSV(errorBuffers, secondErrorFilePath)
    zout.write( secondErrorFilePath, secondErrorFileName)
    zout.write( resultsFilePath, resultsFileName)
    zout.close()

def errors2CSV( errorBuffers, errorFile):
    f = open(errorFile, 'w')
    f.write( "".join( errorBuffers ) )
    f.close()


def marks2ExcelFile( marks, resultsFilePath ):
    df=pd.DataFrame()
    for person, qmark in marks.iteritems():
        df.ix[person, "Name"] = person
        for question in sorted( qmark ):
            df.ix[ person, question ]  = qmark [ question ]

    resultsWriter = pd.ExcelWriter( resultsFilePath )
    df.to_excel(resultsWriter, "Marks", index=False )
    resultsWriter.save()
    return 

def usage():
    print "ha:s:dz:v:, [help, answerfile=, submissionfile=, zipfile=, savefile=]) "


def main(argv):
    answerFile = ""
    submissionFile = ""
    zipFile = ""
    saveFile = ""
    errorFile = None
    try:
        opts, args = getopt.getopt(argv, 
                "ha:s:dz:v:e:", 
                ["help", "answerfile=", "submissionfile=", "zipfile=", "savefile=", "errorfile="]) 
    except getopt.GetoptError:           
        usage()                          
        sys.exit(2)                     
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()                     
            sys.exit()                  
        elif opt == '-d':
            global _debug               
            _debug = 1                  
        elif opt in ("-a", "--answerfile"): 
            answerFile = arg               
        elif opt in ("-z", "--zipfile"): 
            submissionZip   = arg               
        elif opt in ("-s", "--submissionfile"): 
            submissionFile = arg               
        elif opt in ("-v", "--savefile"): 
            saveFile = arg               
        elif opt in ("-e", "--errorFile"): 
            errorFile = arg               

    LOGGER.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    LOGGER.addHandler(ch)
    if answerFile=="" or saveFile=="":
        usage()
        sys.exit()
    if submissionFile=="" and submissionZip=="":
        usage()
        sys.exit()
    if submissionFile != "":
        print processSubmission(answerFile,submissionFile, saveFile)
    elif submissionZip  != "":
        print processSubmissionZip(answerFile,submissionZip, saveFile, errorFile)
    else:
        usage()
    
    

if __name__ == "__main__":
    main(sys.argv[1:])

