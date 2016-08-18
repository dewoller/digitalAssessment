#!/usr/bin/python
# code to read in an xls sheet, return a dict of sheets of values


import sys, getopt, xlrd
import pandas as pd
import logging
import unicodedata
import datetime
LOGGER = logging.getLogger(__name__)
_debug=1

class Reader(object):
    """Read in an excel sheet"""

    def __init__(self, path, isSubmission=True):
        if isSubmission:
            self.getSubmissionExcelSheets( path )
        else:
            self.getMasterExcelSheets( path )
    
    def getSubmissionExcelSheets( self, path ):
        """ 
        Q1 C,D,E, 4-24 prefix, code, convention
        Q1P - DE, 27-47 code, convention
        """
        indexes = {
                'Q1':  {
                        2: 'Prefix',
                        3: 'Code',
                        4: 'Convention'
                        },
                'Q1P': {
                        3: 'Code',
                        4: 'Convention'
                        }
                }
        sheet = xlrd.open_workbook(path).sheet_by_index(0)
        self.dfs={}
        self.dfs[ 'Q1' ] =self.getExcelChunk( sheet, 3, 23, indexes['Q1'].items() )
        self.dfs[ 'Q1P' ] =self.getExcelChunk( sheet, 26, 47, indexes['Q1P'].items() )
    
    def getExcelChunk( self, sheet, start, end, cols ):
        data={}
        for col, name in cols:
            cells = sheet.col_slice(colx=col,
                                    start_rowx=start,
                                    end_rowx=end)
            data[ name ] = list( self.getCellValue( x ) for x in cells  ) 
        
        return pd.DataFrame( data )

    def getCellValue( self, cell ):
        return str(cell.value)

    def getMasterExcelSheets( self, path):
        xl_file = pd.ExcelFile(path)
        self.dfs = {}
        for sheet in xl_file.sheet_names:
            #import ipdb; ipdb.set_trace()
            maxcols=6
            if sheet[-2:-1] == "P":
                maxcols=2

            self.dfs[sheet] = self.sheetElementsRegularize( xl_file.parse(sheet, parse_cols=maxcols ))
            try:
                # throw away errors
                pass
            except:
                LOGGER.error( "Error with sheet %s in file %s "% (sheet, path))
            
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
         
        if isinstance(x, int) or isinstance(x, float) or isinstance(x, datetime.datetime):
            return str(x)
        return(x)

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
    #r = Reader(infile)
    #print(r.dfs[0])
    

if __name__ == "__main__":
    main(sys.argv[1:])

    

