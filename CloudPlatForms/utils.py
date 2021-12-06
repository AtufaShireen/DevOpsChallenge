import pandas as pd
import os
import json
from dotenv import load_dotenv
load_dotenv()
def csv_to_h5(csv_file_path,h5_file_path):
    hdf_key = 'hdf_key'
    store = pd.HDFStore(h5_file_path)
    print('H5 File created for users: ')
    
    for chunk in pd.read_csv(csv_file_path, chunksize=500000):
        store.append(hdf_key, chunk, index=False)
    # store.create_table_index(hdf_key, optlevel=9, kind='full')
    store.close()

def gcp_storage_credentials():
    info = {
  "type": os.environ.get("type"),
  "project_id": os.environ.get("project_id"),
  "private_key_id": os.environ.get("private_key_id"),
  "private_key": os.environ.get("private_key").replace('\\n', '\n'),
  "client_email": os.environ.get("client_email"),
  "client_id": os.environ.get("client_id"),
  "auth_uri": os.environ.get("auth_uri"),
  "token_uri": os.environ.get("token_uri"),
  "auth_provider_x509_cert_url": os.environ.get("auth_provider_x509_cert_url"),
  "client_x509_cert_url": os.environ.get("client_x509_cert_url"),
    }
    return info