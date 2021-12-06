from datetime import date, datetime
from DBManagement.mongops import MongoDBmanagement
from DBManagement.bqops import BigQueryManagement
from ProjectLoggings.loggs import App_Logger
from ValidationProcess.utils import *
import glob
import os
import json
import re
import shutil
import pandas as pd
import logging
class InsertPreprocess:
    def __init__(self,path,user_id,project_id,user_root,type):
        '''Recieve Train and Prediction Folder filter and store aggregated file in bq warehouse'''
        self.raw_folder = path
        self.type=type
        self.bad_folder = os.path.join(user_root,'BADRAWDATA',user_id,project_id)
        self.good_folder = os.path.join(user_root,'GOODRAWDATA',user_id,project_id)
        self.final_folder = os.path.join(user_root,'FINALDATA',user_id,project_id)
        if not os.path.isdir(self.bad_folder):
            os.makedirs(self.bad_folder,exist_ok=True)
        if not os.path.isdir(self.good_folder):
            os.makedirs(self.good_folder,exist_ok=True)
        if not os.path.isdir(self.final_folder):
            os.makedirs(self.final_folder,exist_ok=True)
        self.user_id = user_id
        self.project_id = project_id

        self.mongops = MongoDBmanagement(user_id=user_id,project_id=project_id)
        self.project = self.mongops.findfirstRecord('ProjectData','projects',{'project_id':self.project_id})
        self.bqops = BigQueryManagement(user_id=user_id,project=self.project,type=type)        
        self.logger = App_Logger(user_id,project_id)
    def process_validation(self):
        logging.info(f'Validation of files started')
        try:  
            self.update_file_type()
            self.validatefilename()
            self.validatecolumns()
            self.validatemissingdata()
            if not os.listdir(self.good_folder):
                logging.warning(f"No Good files detected")
                raise ValueError(f'No Good Files Detected')
            logging.info(f'db started')
            self.bqops.create_table()
            self.bqops.insert_table(self.good_folder)
            logging.info(f'dbs done')
        except Exception as e:
            logging.info(f'error{e}')
            raise e
    
    def valuesFromSchema(self):

        if self.type=='train':
            schema = self.project.get('train_schema').replace("\'", "\"")
        else:
            schema = self.project.get('test_schema').replace("\'", "\"")
        dic = json.loads(schema)
        try:
            
            date_stamp=dic['LengthOfDateStampInFile']
            time_stamp=dic['LengthOfTimeStampInFile']
            column_names=dic['ColName']
            noofcolumns=dic['NumberofColumns']
            return date_stamp,time_stamp,column_names,noofcolumns
        except Exception as e:
            logging.info(e)
            raise e
    
    def validatefilename(self):
        logging.info('Validating File Name')
        regex = self.project.get('file_regex').replace('.csv','.h5')
        files = [f for f in os.listdir(self.raw_folder)]
        date_stamp_len,time_stamp_len,column_names,noofcolumns = self.valuesFromSchema()
        if files:
            for file in files:       
                if re.match(regex,file):
                    logging.info(f'Doesnot Match regex')
                    try:
                        filename = file.split('.')[0]
                        _,datestamp ,timestamp = filename.split('_')
                        if (len(datestamp) ==date_stamp_len) and (len(timestamp)==time_stamp_len):
                            shutil.copy(os.path.join(self.raw_folder,file),os.path.join(self.good_folder,file))
                            logging.info(f'good file detected{file}')
                            self.logger.project_logs(f'Good File {file}')
                        else:
                            shutil.copy(os.path.join(self.raw_folder,file),os.path.join(self.bad_folder,file))
                            logging.info(f'bad file detected with name  with datestamp: {file}')
                            self.logger.project_logs(f'Bad File {file} with datestamp',exception=True)
                    except Exception as e:
                        shutil.copy(os.path.join(self.raw_folder,file),os.path.join(self.bad_folder,file))
                        self.logger.project_logs(f'Bad File {file}  with name',exception=True)
                        logging.info(f'bad filee  with name: {e}')

                else:
                    shutil.copy(os.path.join(self.raw_folder,file),os.path.join(self.bad_folder,file))
                    self.logger.project_logs(f'Bad File regex {file}',exception=True)
                    logging.info(f'bad file detected with name: {file}')

    def update_file_type(self):
        logging.info(f'Change csv to hdf for reducing memory')
        raw_folder = [f for f in os.listdir(self.raw_folder)]
        for csv_file_name in raw_folder:
            logging.info(f"---------------FIlename: {csv_file_name} {csv_file_name.split('.')[1]}")
            if csv_file_name.split('.')[1] == '.h5':
                logging.info(f'-----------------------Yes {csv_file_name}')
                continue
            h5_file_name = f"{csv_file_name.split('.')[0]}.h5"
            csv_file_path =os.path.join(self.raw_folder,csv_file_name) 
            h5_file_path = os.path.join(self.raw_folder,h5_file_name)
            try:
                csv_to_h5(csv_file_path,h5_file_path)
                logging.info('Csv file detected')
                if os.path.isfile(csv_file_path):
                    os.remove(csv_file_path)
                    logging.info(f'File removed!')
                    logging.info("csv file removed")
                    logging.info(f"h5 file created: {h5_file_path}")
                    continue
            except Exception as e:
                logging.info("H5 operation could'nt be performed {e}")
                raise e
    
    def validatecolumns(self):
        logging.info('Validate No of columns and Column Names')
        files = [f for f in os.listdir(self.good_folder)]
        _,_,column_names,noofcolumns = self.valuesFromSchema()
        for file in files:
            df = pd.read_hdf(os.path.join(self.good_folder,file))
            if df.shape[1] == noofcolumns:
                for col in column_names.keys():
                    if col in df.columns:
                        continue
                    else:
                        shutil.move(os.path.join(self.good_folder,file),os.path.join(self.bad_folder,file))
                        self.logger.project_logs(f'Bad File {file} with column names',exception=True)
                        logging.info(f'bad file detected with column names: {file}')
            else:
                shutil.move(os.path.join(self.good_folder,file),os.path.join(self.bad_folder,file))
                self.logger.project_logs(f'Bad File {file} no fo columns',exception=True)
                logging.info(f'bad file detected with no of columns: {file}')

    def validatemissingdata(self):
        logging.info(f'Validating missing data')
        files = glob.glob(self.good_folder + '\*', recursive=True)
        for file in files:
            try:
                logging.info(f'-------------------file here: {file}')
                df = pd.read_hdf(os.path.join(self.good_folder,file))
                df.fillna('NULL',inplace=True)
                df.to_hdf(os.path.join(self.good_folder,file),index=None,key='hdf_key')
            except Exception as e:
                self.logger.project_logs(f'Bad File {file} for insertions',exception=True)
                logging.info(f'bad file detected wfro insertion {e}')

# user_id='de32b12f-bdc3-4db5-984d-7c2a3ed03096'
# project_id = '754d0fb8-125c-4658-97e6-4d78708eae67'
# root_dir = r'C:\Users\anony\Projects\AUTOMLOPS'

# train_root = os.path.join(root_dir,'ValidationProcess','TRAIN')
# train_folder = os.path.join(train_root,'RAWDATA',user_id,project_id)
# raw_folder  = os.path.join(train_root,'RAWDATA',user_id,project_id)
# x = InsertPreprocess(path=raw_folder,user_id=user_id,
# project_id=project_id,user_root=train_root,type=type)
# x.process_validation()