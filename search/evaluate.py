"""
======================================================================
======================================================================
               Run evaluation of the results
 Compares journal search results with anticipated results
 
 Note: Both the records hsould be first column of csv
 evaluate.py  <input_file in csv>  <output file in csv>
======================================================================
======================================================================
"""
import os
import sys
import pandas as pd
from fuzzywuzzy import fuzz

input_file = open(sys.argv[1], 'r')
compare_file = open(sys.argv[2], 'r')

predict = []
actual = []
matcount = 0
miscount = 0
totalcount = 0

print('tag, journal, expected, score')

lines = input_file.readlines()
for line in lines:
    jrnl_name = line.split(",")[0]
    jrnl_score = line.split(",")[1].strip('\n')
    comp_line = compare_file.readline().strip('\n')
    comp_line = comp_line.lower()
    
    if comp_line == "no result match":
        predict.append('NoJrnl')
    else:
        predict.append('Jrnl')
        
    if fuzz.ratio(jrnl_name, "no result match") > 80:
        actual.append('NoJrnl')
    else:
        actual.append('Jrnl')
    
    totalcount = totalcount + 1
    #Compare the journal names to find match
    match_ratio = fuzz.ratio(jrnl_name, comp_line)
    if match_ratio < 80:
        miscount += 1
        print("Miss"+","+jrnl_name+","+comp_line+","+jrnl_score)
    else:
        matcount +=  1
        print("Hit"+","+jrnl_name+","+comp_line+","+jrnl_score)

print("==================================")
print("Match : ", matcount, round(matcount*100/totalcount, 2), "%")
print("Miss Match", miscount, round(miscount*100/totalcount, 2), "%")
y_actu = pd.Series(actual, name='Actual')
y_pred = pd.Series(predict, name='Predicted')
df_confusion = pd.crosstab(y_actu, y_pred)
print(df_confusion)




    