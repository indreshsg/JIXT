"""
######################################################################
######################################################################
                    Build Index
    
Build an index from the Journal Database for searching

Copyright: (c) 2016, Indresh Sira, The Ohio State University
All rights reserved.
######################################################################
######################################################################
"""
import os
import sys, getopt
from whoosh.index import create_in
from whoosh.fields import *

def HelpMsg():
    print('Check your command line arguments !!!!')
    print('build.py -i <DBFile> -o <OutFolder> -l | ')
    print('-h for Help')
    print('-l for delimiter')


def build_index(inputfile, outfolder, delimiter):
    schema = Schema(title=TEXT(stored=True), content=TEXT(stored=True))

    #Create and index folder and commit the values from journal database
    if not os.path.exists(outfolder):
        os.mkdir(outfolder)
    ix = create_in(outfolder, schema)
    
    writer = ix.writer()
    #convert all lines in file to index 
    with open(inputfile, 'r', encoding="utf-8") as dbFile:
        next(dbFile)
        for line in dbFile:
            fields = line.split(delimiter)
            title_field = fields[0].strip().replace('\t', '').lower()
            content_field = fields[1].strip().replace('\t', '').lower()
            writer.add_document(title = title_field,
                                content = content_field)
    writer.commit()

"""
----------------------------------------------------------------------
    Command Line Arg and File check starts from Here
----------------------------------------------------------------------
"""
def start(argv):
    inputfile = ''
    outputfolder = ''
    delimiter = ''
    try:
        opts, args = getopt.getopt(argv,"hi:o:l:", \
                               ["ifile=","ofile="])
    except getopt.GetoptError:
        HelpMsg()
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            HelpMsg()
            sys.exit()
        elif opt in ("-i", "--ifile"):
            inputfile = arg
        elif opt in ("-o", "--ofile"):
            outputfolder = arg
        elif opt == '-l':
            delimiter = arg
            
    #build Index file
    build_index(inputfile, outputfolder, delimiter)

if __name__ == "__main__":
    start(sys.argv[1:])
    
