"""
######################################################################
######################################################################
                        Year Search
    
Descp: Searches for year in the given string and etxracts the 
information. Uses NLP to look for sequence of numbers to extract 
and then chooses the 4 letter number between 1990-2016

Copyright: (c) 2016, Indresh Sira, The Ohio State University
All rights reserved.
######################################################################
######################################################################
"""
import nltk
import sys
import datetime

latest_year = datetime.datetime.now().year
early_year = latest_year - 150

def get_year(input_str):
    text = nltk.word_tokenize(input_str)
    tagged_token = nltk.pos_tag(text)
    
    year = None
    #Search through the tagged tokens for numbers 'CD'
    for each in tagged_token:
        [key, tag] = each
        if key.isdigit() and tag == 'CD':
            val = int(key)
            if val >= early_year and val < latest_year:
                year = val
    
    return year
    
 
### If run as standlone, run a test 
if __name__ == "__main__": 
    out = open(sys.argv[2], 'w')
    with open(sys.argv[1], 'r') as file:
        while True:
            line = file.readline()
            string = line.split(",")
            info_str = ",".join(string[1:])
            try:
                year = get_year(info_str)
            except:
                print(info_str)
            out.write(str(year) + '\n')
    out.close()
    