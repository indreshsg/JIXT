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
from fuzzywuzzy import fuzz
import jellyfish

input_file = open(sys.argv[1], 'r')
compare_file = open(sys.argv[2], 'r', errors='ignore')

matcount = 0
miscount = 0
false_Positive = 0
false_Negitive = 0
true_Positive = 0
true_Negitive = 0
totalcount = 0

print('tag, journal, expected, score')

lines = input_file.readlines()
for line in lines:
    jrnl_name = line.split(",")[0].lower()
    jrnl_score = line.split(",")[2].strip('\n')
    comp_line = compare_file.readline().strip('\n')
    comp_line = comp_line.split(",")[0].lower()
        
    isNOMatch = True
    if fuzz.ratio(comp_line, "no result match") > 95:
        isNOMatch = False
            
    totalcount = totalcount + 1
    #Compare the journal names to find match
    match_ratio = jellyfish.jaro_distance(jrnl_name, comp_line)
    #match_ratio = fuzz.ratio(jrnl_name, comp_line)
    if match_ratio < 0.85:
        miscount += 1
        if isNOMatch == False:
            false_Negitive += 1
        else:
            false_Positive += 1
        print("Miss"+","+jrnl_name+","+comp_line+","+jrnl_score)
    else:
        matcount +=  1
        if isNOMatch == False:
            true_Negitive += 1
        else:
            true_Positive += 1
        print("Hit"+","+jrnl_name+","+comp_line+","+jrnl_score)

totPositives = true_Positive +  false_Positive  
totNegatives = false_Negitive + true_Negitive
print("==================================")
print("Match : ", matcount, round(matcount*100/totalcount, 2), "%")
print("Miss Match", miscount, round(miscount*100/totalcount, 2), "%")
print("==================================")
print("Predicted         Jrnl      ||      NoJrnl")
print("Expected")
print("Jrnl           %d(%.2f)     ||    %d(%.2f)" % ( true_Positive,
                                                  round(true_Positive*100/totPositives, 2),
                                                  false_Positive, 
                                                  round(false_Positive*100/totPositives, 2) ))
print("NoJrnl         %d(%.2f)     ||    %d(%.2f)" % ( false_Negitive,
                                                  round(false_Negitive*100/totNegatives, 2),
                                                  true_Negitive, 
                                                  round(true_Negitive*100/totNegatives, 2) ))

