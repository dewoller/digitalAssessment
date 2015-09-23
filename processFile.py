


import sys, getopt
import pandas as pd
import zipfile
import tempfile
import logging
import xls2dict
import calculateMark
import os
import ntpath
LOGGER = logging.getLogger( __name__)
_debug=0

def processSubmission( answerFile, submissionFile, resultsFile):
    modelAnswerReader = xls2dict.Reader(answerFile, isSubmission=False) 
    submissionReader = xls2dict.Reader(submissionFile) 
    #resultsFile = submissionFile + ".results.xlsx"
    resultsWriter = pd.ExcelWriter(resultsFile)
    marker=calculateMark.Marker()
    perSheetMarks = {}
    for sheet in sorted(modelAnswerReader.getSheetNames()):
        if _debug==1:
            print "%s" % sheet
        marker.prepareAnswer(modelAnswerReader.getSheet( sheet ))
        (resultSheet, marks) = marker.mark( submissionReader.getSheet( sheet ))
        #import pdb;pdb.set_trace()
        resultSheet.to_excel(resultsWriter, sheet, index=False)
        perSheetMarks[ sheet ] = marks

    resultsWriter.save()
    return perSheetMarks


def processSubmissionZip( answerFile, submissionZip, outZip):
    tmpInDir = tempfile.mkdtemp()
    tmpOutDir = tempfile.mkdtemp()
    resultsFileName = "__Marks.xlsx"
    resultsFile =  tmpOutDir + os.path.sep + resultsFileName
    marks={}
    zout = zipfile.ZipFile( outZip, "w")
    with zipfile.ZipFile(submissionZip, "r") as z:
        for name in z.namelist():
            z.extract( name, tmpInDir )
            baseName =ntpath.basename(name) 
            inFile = tmpInDir + os.path.sep + name
            if _debug==1:
                print "FILE=\n\"%s\"\n" % inFile 
            outFile= tmpOutDir + os.path.sep + baseName
            marks[ baseName ] = processSubmission(answerFile, inFile, outFile)
            zout.write(outFile, baseName)
    marks2ExcelFile(marks, resultsFile)
    zout.write( resultsFile, resultsFileName)
    zout.close()

def marks2ExcelFile( marks, resultsFile ):
    df=pd.DataFrame()
    for person, qmark in marks.iteritems():
        df.ix[person, "Name"] = person
        for question in sorted( qmark ):
            df.ix[ person, question ]  = qmark [ question ]

    resultsWriter = pd.ExcelWriter( resultsFile )
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
    try:
        opts, args = getopt.getopt(argv, "ha:s:dz:v:", ["help", "answerfile=", "submissionfile=", "zipfile=", "savefile="]) 
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
            zipFile = arg               
        elif opt in ("-s", "--submissionfile"): 
            submissionFile = arg               
        elif opt in ("-v", "--savefile"): 
            saveFile = arg               

    LOGGER.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    LOGGER.addHandler(ch)
    if answerFile=="" or saveFile=="":
        usage()
        sys.exit()
    if submissionFile=="" and zipFile=="":
        usage()
        sys.exit()
    if submissionFile != "":
        print processSubmission(answerFile,submissionFile, saveFile)
    elif zipFile != "":
        print processSubmissionZip(answerFile,zipFile, saveFile)
    
    

if __name__ == "__main__":
    main(sys.argv[1:])

