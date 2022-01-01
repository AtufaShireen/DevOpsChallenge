import json
from google.cloud import bigquery
import os
import pandas as pd
from google.oauth2 import service_account
from google.cloud import bigquery
import logging
from CloudPlatForms.utils import gcp_storage_credentials
# Download query results.


class BigQueryManagement():
    def __init__(self,project,user_id,type) -> None:
        self.root_project = 'automlops' 
        credentials = service_account.Credentials.from_service_account_info(gcp_storage_credentials())
        self.client = bigquery.Client(project=self.root_project,credentials=credentials)
        
        self.project = project
        self.user_id=user_id.replace('-','_')
        self.proj_cat = project.get('mltype')
        self.project_name = project.get('project_title')
        self.table_id = f"{self.root_project}.{self.user_id}.{type}-{ self.project_name}"
        self.type=type
    
    def create_table(self):  
        dataset = self.client.create_dataset((self.user_id).replace('-','_'),exists_ok=True)
        try:
            print('check if table exists')
            dataset = self.client.delete_table(self.table_id)
            print('deleting existing table')
        except Exception as e:
            print('table not found,createing')
        try:
            self.client.create_table(self.table_id)
            print('Table createad')
        except Exception as e:
            print('Table cannot be created')
        return True
    
    def insert_table(self,folder_path): 
        import glob
        files = glob.glob(folder_path + '\*', recursive=True)
        schema = []
        if type=='train' or self.proj_cat=='customersegmentation':
            cols = json.loads(self.project.get('train_schema').replace("\'", "\""))
        else:
            print('--------',self.proj_cat)
            cols = json.loads(self.project.get('test_schema').replace("\'", "\""))
        column_names = cols.get('ColName')
        for key,value in column_names.items():
            schema.append(bigquery.SchemaField(key,value))
        print("Schema",schema)
        for f in files:
            if f.endswith('.h5'):
                df = pd.read_hdf(f)
            else:
                df = pd.read_csv(f)
            job_config = bigquery.LoadJobConfig(schema=schema)
            try:
                job = self.client.load_table_from_dataframe(df, self.table_id,job_config=job_config)
                continue
            except Exception as e:
                print('Bad FIle For Insertion!',e)
                raise e
         
        return True
    
    def load_data(self,final_path):
        print('Loading data to final path')
        query_string = f"""
        SELECT
        *
        FROM `{self.table_id}`
        """

        dataframe = (
            self.client.query(query_string)
            .result()
            .to_dataframe(
                create_bqstorage_client=False,
            )
        )
        filename = f"{os.path.join(final_path,self.project_name)}_{self.type}.csv"
        logging.info(f'-------------------------fiekname----------- {filename}')
        # dataframe.to_hdf(filename,index=False,key='df')
        dataframe.to_csv(filename,index=False)
        logging.info('File moved to FinalData')
        del dataframe
        return filename
    
    def delete_table(self):
        self.client.delete_table(self.table_id,not_found_ok=True)

# import mongops

# proj = '1deeab0c-c187-4bce-bb82-ae56cbfb1e19'
# user_id = 'de32b12f-bdc3-4db5-984d-7c2a3ed03096'
# mng = mongops.MongoDBmanagement(user_id,proj)
# projects = mng.findfirstRecord('ProjectData','projects',{'project_id':proj})
# print(projects.get('train-schema'))
# type='train'
# d = BigQueryManagement(projects,user_id,type)
# d.insert_table(r"C:\Users\anony\Projects\AUTOMLOPS\TrainingProcess\train_data\de32b12f-bdc3-4db5-984d-7c2a3ed03096\79029333-9a56-4385-abc5-201386a86023")
