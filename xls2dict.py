#!/usr/bin/python
# code to read in an xls sheet, return a dict of sheets of values


import sys, getopt
import pandas as pd
import logging
logger = logging.getLogger( __name__)


class Reader:

    def __init__(self, filename):
        xl_file = pd.ExcelFile(filename)
        i=0
        self.dfs={}
        for sheet in xl_file.sheet_names:
            # throw away 
            try:
                self.dfs[i] = xl_file.parse(sheet)
                i+=1
            except:
                pass


def usage():
    print """ Usage: %s 
    h=help
    f file = file to parse
    """ % (sys.argv[0])

def main(argv):
    infile="answer.xlsx"
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

    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    r = Reader(infile)
    print(r.dfs[0])
    

if __name__ == "__main__":
    main(sys.argv[1:])

    

