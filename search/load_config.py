"""
######################################################################
######################################################################
                        Load config
    
Descp: WIll parse the config XML file and update the config object

Copyright: (c) 2016, Indresh Sira, The Ohio State University
All rights reserved.
######################################################################
######################################################################
"""
import xml.etree.ElementTree as ET

xml_conf = "config.xml"

class load_config:
    
    index_foldr = None
    DB_file = None
    java_home = None
    NER_jar = None
    NER_model = None
    
    #parse the config file and load the information
    def __init__(self):
        conf_tree = ET.parse(xml_conf)
        root = conf_tree.getroot()

        #------ Get the Whoosh and Ref Journal location ------
        #Get the folder name from the config file
        journal_db = root.find('journal_db_index')
        self.index_foldr = journal_db.get('path')
        #Get the db file name
        journal_db_file = root.find('journal_db_file')
        self.DB_file = journal_db_file.get('path')
        
        #------ Get the Java and NER package info location ------
        self.java_home = root.find('java_home').get('path')
        self.NER_jar = root.find('ner_jar_file').get('path')
        self.NER_model = root.find('ner_model_file').get('path')
        
        
        