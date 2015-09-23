#!/usr/bin/python
# code to read in an xls sheet, return a dict of sheets of values


import sys, getopt
import pandas as pd
import logging
import unicodedata
import datetime
LOGGER = logging.getLogger(__name__)
_debug=1

class Reader(object):
    """Read in an excel sheet"""

    def __init__(self, filename, isSubmission=True):
        xl_file = pd.ExcelFile(filename)
        self.dfs = {}
        for sheet in xl_file.sheet_names:
            #import ipdb; ipdb.set_trace()
            maxcols=3
            if sheet[-2:-1] == "P":
                maxcols=2

            if not isSubmission:
                maxcols  = maxcols + 3

            self.dfs[sheet] = self.sheetElementsRegularize( xl_file.parse(sheet, parse_cols=maxcols ))
            try:
                # throw away errors
                pass
            except:
                LOGGER.error( "Error with sheet %s in file %s "% (sheet, filename))
            
    def getSheet(self, name):
        """ get sheet of name """
        try:
            return self.dfs[name]
        except:
            return None

    def getSheetNames(self):
        """ get sheet names """
        return self.dfs.keys()

    def colToString(self, col ):
        return col.map( lambda f: self.elementToString(f) )

    def elementToString(self, x ):
        if isinstance(x, str):
            return unicode(x, "utf-8")
        if isinstance(x, unicode):
            return x
        if isinstance(x, int) or isinstance(x, float): 
            return unicode(str(x), "utf-8")
        if isinstance(x, datetime.datetime):
            return unicode(str(x), "utf-8")

        return unicode(str(x), "utf-8")


    def sheetElementsRegularize( self, sheet ):
        if len(sheet)==0:
            return sheet
        return sheet.fillna("").apply( lambda f: self.colToString(f), axis=1)




def usage():
    print (""" Usage: %s
    h=help
    f file = file to parse
    """ % (sys.argv[0]))

def main(argv):
    infile = "answer.xlsx"
    try:
        opts, args = getopt.getopt(argv, "hf:d", ["help", "file="]) 
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
        elif opt in ("-f", "--file"): 
            infile = arg               

    LOGGER.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    LOGGER.addHandler(ch)
    r = Reader(infile)
    print(r.dfs[0])
    

if __name__ == "__main__":
    main(sys.argv[1:])

    

