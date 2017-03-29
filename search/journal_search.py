"""
######################################################################
######################################################################
                        Journal Search
    
Descp: Searches for journal names from the index created by Whoosh
if match is found returns the title of the match

To Execute Issue:
    mpirun -np <No_Processor> python <parent_code.py>
    
Copyright: (c) 2016, Indresh Sira, The Ohio State University
All rights reserved.
######################################################################
######################################################################
"""
import re
import os
import sys
import time
import io

import whoosh.index as index
from whoosh.fields import *
from whoosh.qparser import QueryParser
from whoosh.qparser import MultifieldParser
import whoosh.qparser as Qparser
from whoosh.query import FuzzyTerm
from whoosh import scoring

from fuzzywuzzy import process
import load_config
import jellyfish
import author_tagger
import tame_string as tame_str

glbl_quote_marker = 'aaaa'
No_ResultMatch__ = "No result match"

"""
Check if a given string has any digit
"""
def hasNumbers(inputString):
    return any(char.isdigit() for char in inputString)
    
"""
writes the result to stdout and result Log file
"""
def createLog(msgLst, outFile):
    [journal, title, score] = msgLst
    #Write the result to result FIle
    if journal is None:
        outFile.write("No Journal match, 0 \n")
    else:
        outFile.write(journal + ", " + title +", " + str(score) + '\n')
        
"""
creates Ngram from a list
"""
def list_Ngrams(input_list, n):
  return list(zip(*[input_list[i:] for i in range(n)]))
    
    
"""
Remove any http links present in the text
"""
def strip_http(full_string):
    http_index = full_string.find("http")-1
    full_string = full_string[:http_index]
    return full_string
    
"""
provides sequence match ratio between a string and list
"""
def similar(srch_str, lookup_lst):
    high_score = 0.0
    match_title = ''
    for each_item in lookup_lst:
        score = jellyfish.jaro_distance(srch_str, each_item)
        #print(srch_str + "|" + each_item + "|" + str(score))
        if score > high_score:
            match_title = each_item
            high_score = score
    #print("########" + match_title + "|" + str(high_score))
    return [match_title, high_score]

"""
Get the index of the first marker from the given string
"""
def marker_index(full_string):
    spec_chars = set(""":?'";.,0123456789!()~#@^&$%*{}|""")
    for chars in full_string:
        if chars in spec_chars:
            return full_string.index(chars)
    return len(full_string)
    
"""
finds a probable full name by using markers like : , ' etc
returns the probable name
"""    
def strip_using_marker(full_string, key_word):
    full_string = strip_http(full_string)
    
    #remove any of the following ()-?
    full_string = re.sub('[-]', '', full_string)
    full_string = re.sub('[\|/]', ' ', full_string)
        
    if key_word not in full_string:
        return None
        
    pivot = full_string.index(key_word)
    #Search for any special character from the pivot   
    rvrse_fullstr = ''.join(reversed(full_string[:pivot]))
        
    start_index = pivot - marker_index(rvrse_fullstr)
    end_index = marker_index(full_string[pivot:]) + pivot
    
    #Get full name and removes any spaces in from or back
    prob_name = full_string[start_index:end_index]
    
    #Check if et al is present and name and remove anything before it
    prob_lst = prob_name.split(' ')
    for i in range(0, len(prob_lst)):
        if prob_lst[i] == 'al':
            prob_name = (' ').join(prob_lst[i+1:])
            break  
                    
    return prob_name.strip()
    
"""
PIVOT RATIO: gives the ratio of length of pivot string with 
respect to the entire marker seperated string
"""
def pivot_ratio(full_string, key_word):
    marked_string = strip_using_marker(full_string, key_word)
    if marked_string:
        ratio = len(key_word)/len(marked_string)
    else:
        ratio = 0
    return ratio

"""
Check if a given list has 'Journal' present, if so extract the journal
name from the string
"""
def hasJournal(journal_lst, info_str):
    id = 0
    end = 0
    isPresent = False
    
    #Fisrt do a simple search for keyword journal
    word_lst = [word.lower() for word in journal_lst]
    if 'journal' in word_lst:
        id = word_lst.index('journal')
        isPresent = True
    elif 'patent office' in word_lst or 'uspto' in word_lst:
        return [True, 'No journal match']
    else:
        return [isPresent, None]
      
    #If name journal is present, get the full name of journal
    #NOTE: end of name is usually marked by presence of number 
    #or a special charcter ',' in the end
    journal_name = strip_using_marker(info_str.lower(), 'journal')
            
    return [isPresent, journal_name]
    
"""
Gets the index from the first character of journal name
"""
"""
def get_alphaindex(name):
    eucld_mean_val = 0
    true_len = 0
    name = name.lower()
    name = name.strip()
    first_word = name.split()[0]
    for i in range(0, len(first_word)):
        char = first_word[i]
        if (char != ' ' and char != '-' and   \
            char != '_' and char.isdigit() != True):
            eucld_mean_val += (ord(char) - ord('a'))
            true_len += 1
    if true_len == 0:
        return 0
    bin = int((eucld_mean_val/ true_len))
    if bin < 0:
        msg = 'Error in finding bin! Bin Value= ' + str(bin)
        sys.stdout.write(msg)
    else:
        return bin
"""
 
def get_alphaindex(name):
    alpha_index = name.lower()   
    
    if alpha_index.isdigit():
        alpha_index = 0
    else:
        alpha_index = ord(alpha_index) - ord('a') + 1
        
    alpha_index = 0 if alpha_index > ord('z') else alpha_index
    if alpha_index < 0:
        alpha_index = 0 
    return alpha_index
    
"""
Search for quotes in the line and return the end of quotes
If no quotes found return -1
"""
def strip_Quote(line_str, quote_marker=None):
    global glbl_quote_marker
    if quote_marker is None:
        quote_marker = glbl_quote_marker
        
    #Remove any apostrophe if found
    line_str = re.sub(r"'s ", ' ', line_str)
    strlen = len(line_str)
    srch_char = "'"
    #Get the firts and last occurence, if either -1, it indicates error
    first = line_str.find(srch_char)
    last = line_str.find(srch_char, first+1)
    #If the no of quotes is odd, return the same string back, else strip
    if first is -1 or last is -1:
        strip_strng =  line_str
        marked_strng = " "
    else:
        strip_strng = line_str[:first] + quote_marker + line_str[last+1:]
        marked_strng = line_str[first+1:last]
        
    return [strip_strng, marked_strng]
    
""" 
Remove any numbers and split the string based on comma
"""
def sanitize(journal_str):
    #Remove vol or volume label
    sant_str = re.sub("(?i)vol\.","",journal_str)
    sant_str = re.sub("(?i)volume\.","",sant_str)
    
    #Remove any hyperlink in the text
    sant_str = strip_http(sant_str)
                       
    #Remove any quotes if present
    [sant_str, marked_strng] = strip_Quote(sant_str)
    
    #Remove any special character and number
    sant_str = re.sub('[^\wA-Za-z]', ' ', sant_str)
    sant_str = re.sub('\d+', ' ', sant_str)
    
    jrnl_lst = sant_str.split()
    return jrnl_lst
        
"""
From a given list of words, creates N-gram bucket pool
Removes any numbers or special characters if present
"""   
def create_Ngram(str_bucket):
    global glbl_quote_marker
    #Remove special characters, numbers and then et al
    str_bucket = [re.sub(r'\bet\b', ' ', each) for each in str_bucket]
    str_bucket = [re.sub(r'\bal\b', ' ', each) for each in str_bucket]
    str_bucket = [re.sub(r'\boffice\b', ' ', each) for each in str_bucket]
    str_bucket = [re.sub(r'\bpatent\b', ' ', each) for each in str_bucket]
    str_bucket = [re.sub(r'\bno\b', ' ', each) for each in str_bucket]
    str_bucket = [re.sub(r'\beuropean\b', ' ', each) for each in str_bucket]
    str_bucket = [re.sub(r'\bny\b', ' ', each) for each in str_bucket]
    str_bucket = [re.sub(r'\bunited states of america\b', 'usa', each) for each in str_bucket]
    str_bucket = [re.sub(r'\b am j \b', 'american journal', each) for each in str_bucket]
      
    #Remove empty elemnts from end of list
    if str_bucket:
        while not str_bucket[-1]:
            str_bucket.pop()
        
    #Combine multiple spaces into one
    str_bucket = " ".join(str_bucket).split()
    
    #remove quote_marker and replace with double space
    if glbl_quote_marker in str_bucket:
        str_bucket[str_bucket.index(glbl_quote_marker)] = "    "
    
    #Create Gram from list
    Ngram_lst = []
    bucket_len = len(str_bucket)
    for gram in range(2, bucket_len):
        gram_list = list_Ngrams(str_bucket, gram) #create N gram list
        for each in gram_list:
            srch_word = " ".join(each)
            Ngram_lst.append(srch_word)
           
    return Ngram_lst
        
######################################################################
######################################################################
#ournal DB Table Infor
#Min length : 2 
#Max length: Title = 235 and abbrevation = 21
#Min word length: 1
#Max wod length: Title = 31 and abbrevation = 7

"""
Journal Search Class:
sanitize :: will remove any keyword called vol or volume and generate
            a list of words
jrnl_srch :: will first search for word 'Journal' if not present will
            initiate a complex N-gram search through the index file
"""
class jrnl_srch:
    #Load and open the index directory from xml file       
    def __init__(self, log_en):
        config = load_config.load_config()
        index_dir = config.index_foldr
        dbFileName = config.DB_file
        ix = index.open_dir(index_dir)
        self.authr_Tag = author_tagger.author_tag()
        #--------------- READ & CREATE THE DATABASE ----------------------#
        self.jrnl_DB_name_lst = [[]* 27 for i in range(27)]
        self.jrnl_DB_abbrv_lst = [[]* 27 for i in range(27)]   
        DB_index = 0
        #Read DB file and hold a list of all journals    
        with open(dbFileName, 'r') as dbcsvFile:
            db_lines = dbcsvFile.readlines()
            for db_line in db_lines:
                [name, abbrv, type] = db_line.strip('\n').split("|")
               
                alpha_index = get_alphaindex(name[0].lower())
                                
                self.jrnl_DB_name_lst[alpha_index].append(name.lower())
                self.jrnl_DB_abbrv_lst[alpha_index].append(abbrv.lower())
                
                DB_index = DB_index + 1  

        #------------- Create Searher Object for Whoosh -------------------#
        self.searcher = ix.searcher()#weighting=scoring.TF_IDF())
        self.title_parser = MultifieldParser(["title", "content"], ix.schema)
        self.title_parser.add_plugin(Qparser.FuzzyTermPlugin())
        if log_en is True:
            self.log_file = open('debug_results.txt', 'w')
        else:
            self.log_file = None

       
    def try_journal(self, srch_str):
        print(srch_str)
        srchquery = self.title_parser.parse(srch_str)
        results = self.searcher.search(srchquery)
        for i in range(0, results.scored_length()):
            print(results[i]['title'], results.score(i))

    """
    Perform a fuzzy search over DB and create a list of matching context
    """
    def fuzzy_search(self, srch_result_lst):
        title_repo = []
        abbrv_repo = []
        #For each result, serach for matching Levengshtein distance
        for i in range(0, len(srch_result_lst)):
            [srch_str, result] = srch_result_lst[i]
            
            if self.log_file != None:         
                self.log_file.write(srch_str + '\n')
            
            alpha_index = get_alphaindex(srch_str.strip(" ")[0])
            
            try:
                title_match = process.extract( srch_str,   \
                                               self.jrnl_DB_name_lst[alpha_index], \
                                               limit=5)
            except:
                print("Index Error:", alpha_index, srch_str)
                exit()
            abbrv_match = process.extract( srch_str, \
                                           self.jrnl_DB_abbrv_lst[alpha_index], \
                                           limit=5)             
            for each_title in title_match:
                title_repo.append(each_title[0])
                
            for each_abbrv in abbrv_match:
                abbrv_text = each_abbrv[0]
                abbrv_index = self.jrnl_DB_abbrv_lst[alpha_index].index(abbrv_text)
                abbrv_repo.append([each_abbrv[0], abbrv_index])
                
        return [title_repo, abbrv_repo]
        
    def get_best_match(self, Ngram_lst, full_str, threshold):
        global No_ResultMatch__
        title_srch_result = []
        positive_grams = []
        #Search through the title list for matches and hold highest score
        for gram_str in Ngram_lst:
            srch_str = strip_using_marker(full_str, gram_str)
                
            #Continue is string is empty or its just single letter
            if srch_str is None:
                continue           
            if sum(c != ' ' for c in srch_str) <= 3:
                continue
                                
            if len(srch_str) != 0 and srch_str not in positive_grams:                
                title_srch_result.append([srch_str, None])
                #Store the first search the resulted in a hit
                positive_grams.append(srch_str)
                                
        #Create a repositry of matching context and title from fuzzy search
        [title_repo, abbrv_repo] = self.fuzzy_search(title_srch_result)
        
        final_lst = []
        abbrv_name_repo = [i[0] for i in abbrv_repo]
        abbrv_indx_repo = [i[1] for i in abbrv_repo]
        #From the first hit in Ngram search, perform another fuzzzy search
        for gram_str in positive_grams:
            [nearest_title, title_score] = similar(gram_str, title_repo)
            [nearest_abbrv, abbrv_score] = similar(gram_str, abbrv_name_repo)
            
            if title_score >= abbrv_score:
                title = nearest_title
                score = title_score
            else:
                alpha_index = get_alphaindex(nearest_abbrv.strip(" ")[0])
                abbrv_index = abbrv_indx_repo[abbrv_name_repo.index(nearest_abbrv)]
                try:
                    title = self.jrnl_DB_name_lst[alpha_index][abbrv_index]
                    score = abbrv_score
                except:
                    continue
            sys.stdout.write('*** '+str(gram_str)+'\n')    
            sys.stdout.write("%s %f\n" % (title, score))
            match_dict = {'title':title,'score':score,'str':gram_str}
            final_lst.append(match_dict)

        max_score = 0
        #Get value with highest score and highest length
        if final_lst:
            max_dict = max(final_lst, key=lambda item:item['score'])
            max_score = max_dict['score']
        
        #Threshold to classify journal names
        if max_score < threshold:
            return [No_ResultMatch__, max_score, None]
               
        best_indx = []
        for i in range(0, len(final_lst)):
            match_dict = final_lst[i]
            if match_dict['score'] == max_score:
                best_indx.append([match_dict['title'], len(match_dict['str'])])
        best_len = [i[1] for i in best_indx]
        max_len_indx = best_len.index(max(best_len))
        best_title = best_indx[max_len_indx][0]
            
        return [best_title, max_score, final_lst]
                      
    #Search for journal name across indexed database
    def get_journal(self, info_str): 
        global No_ResultMatch__
        #First sanitize the input string
        journal_lst = sanitize(info_str)
        #Convert everything to lower case
        journal_lst = [each.lower() for each in journal_lst]    
        [manirated_info_str, article_title] = strip_Quote(info_str.lower()," '")
        manirated_info_str = tame_str.manirate_citation(manirated_info_str)
        #manirated_info_str = self.authr_Tag.rmv_authors(manirated_info_str)
        
                
        ##------- Level 1: Search for 'journal' Tag --------
        #Check if text:'journal' is present
        [isPresent, journal_name] = hasJournal(journal_lst, info_str)
        if isPresent is True:
            alpha_index = get_alphaindex(journal_name.strip(" ")[0])
            prob_title_match = process.extractOne( journal_name,   \
                                                  self.jrnl_DB_name_lst[alpha_index])
            if prob_title_match[1] > 95:
                return [prob_title_match[0], prob_title_match[1], article_title]
        
        if self.log_file != None:         
            self.log_file.write(" ".join(journal_lst) + '\n')
        
        ##------- Level 2: 1-Gram Search --------
        #Search through 1-gram for best batch
        [best_title, max_score, final_lst] =  self.get_best_match(journal_lst, \
                                                   manirated_info_str, \
                                                   0.85)
        if  best_title != No_ResultMatch__:
            return [best_title, max_score, article_title]
                                                           
        ##------- Level 3: N-Gram Pivoted Search --------
        #Create an Ngram list for first parsing
        Ngram_lst = create_Ngram(journal_lst)  
        [best_title, max_score, final_lst] =  self.get_best_match(Ngram_lst, \
                                                    manirated_info_str, \
                                                    0.85)
        return [best_title, max_score, article_title]
                  
"""
Executes journal extarction on single line and collects data
"""
def execute_job(srch, line):
    global No_ResultMatch__
    myIO = io.StringIO()
 
    string = line.split(",")
    info_str = ",".join(string[1:])
    info_str = str(line)
        
    journal = No_ResultMatch__
    score = 0
    title = " "
    
    try:
        sys.stdout.write(info_str)
    except:
        myIO.write("Unicode Error Detected\n")
        return[journal, score, title, myIO]
    
    #Swap the IO's
    my_stdout = sys.stdout
    sys.stdout = myIO

    try:
        [journal, score, title] =  srch.get_journal(info_str)    
        if journal == No_ResultMatch__:
            title = " "
    except:
        pass
    
    sys.stdout = my_stdout
    
    return[journal, score, title, myIO]

### If run as standlone, run a test 
if __name__ == "__main__" and sys.platform == 'linux': 
    from mpi4py import MPI
    avg_time = 0
    no_lines = int(sys.argv[3])
    start_line = int(sys.argv[4]) - 1
    
    #Distribute the task to cores
    comm = MPI.COMM_WORLD
    size = comm.Get_size()
    rank = comm.Get_rank()
    
    srch = jrnl_srch(False)

    if rank == 0:            
        out = open(sys.argv[2], 'w', errors='ignore')
        with open(sys.argv[1], 'r', encoding='utf-8', errors='ignore') as file:
            #Skip to start line
            for j in range(start_line):
                try:
                    file.readline()
                except:
                    continue
            
            
            total_line = no_lines
            while(no_lines > 0):
                strt = time.time()
                
                #Enumerate the workload distribution
                enum_procsr = [0]*size
                for proc in range(0, size):
                    if no_lines > 0:
                        enum_procsr[proc] = total_line - no_lines + 1
                        no_lines -= 1
                    
                for proc in range(1, size):
                    if enum_procsr[proc] != 0:
                        line = file.readline()
                        comm.send(line, dest=proc, tag=1) 
                                
                line = file.readline()                                                
                #Execute the Task
                [journal, score, title, myIO] = execute_job(srch, line)
                
                for proc in range(1, size):
                    if enum_procsr[proc] != 0:
                        msg = comm.recv(source=proc, tag=2)
                        createLog(msg, out)
                                            
                sys.stdout.write(myIO.getvalue())
                sys.stdout.flush()
                createLog([journal, title, score], out)
                                        
                end = time.time() - strt
                avg_time = avg_time + end
                sys.stdout.write('##############################\n')
                sys.stdout.flush()
        #Send Exit message to all threads
        for proc in range(1, size):
            comm.send("Exit", dest=proc, tag=1) 
        sys.stdout.write('Complete!!! --> Average time per serach = %f\n' %(avg_time/total_line))
        sys.stdout.flush()
        out.close()
    else:
        while(True):
            line = comm.recv(source=0, tag=1)
            if line == "Exit":
                break
            [journal, score, title, myIO] = execute_job(srch, line)
            
            sys.stdout.write(myIO.getvalue())
            sys.stdout.write('##############################\n')
            sys.stdout.flush()
            
            myMsg = [journal, title, score]
            comm.send(myMsg, dest=0, tag=2)
            
        sys.stdout.write("Terminating Job %d" %(rank))
##If platform is win32, standalone script
elif __name__ == "__main__" and sys.platform == 'win32':
    srch = jrnl_srch(False)
    avg_time = 0
    out = open(sys.argv[2], 'w', errors='ignore')
    no_lines = int(sys.argv[3])
    start_line = int(sys.argv[4]) - 1
    with open(sys.argv[1], 'r', encoding='utf-8', errors='ignore') as file:
        #Skip to start line
        for j in range(start_line):
            try:
                file.readline()
            except:
                continue
            
        for i in range(no_lines):
            strt = time.time()
                
            line = file.readline()                
                                                             
            #Execute the Task
            [journal, score, title, myIO] = execute_job(srch, line)
                
            sys.stdout.write(myIO.getvalue())
            sys.stdout.flush()
            createLog([journal, title, score], out)
                
            end = time.time() - strt
            avg_time = avg_time + end
            print('Line : ', i,'|| Time taken = ', end)            

    print('Complete!!! --> Average time per serach = ', (avg_time/no_lines))
    out.close()
    
                