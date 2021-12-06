from google.cloud import storage
from google.oauth2 import service_account
from CloudPlatForms.utils import  gcp_storage_credentials
import datetime
import os
import glob

class GCPOps():
    #add path to user buket
    def __init__(self,user_id,user_name,project_id,root_bucket='auto-mlops',root_project='ineuronchallenge' ):

        self.credentials = service_account.Credentials.from_service_account_info(gcp_storage_credentials())
        # self.root_project = root_project
        self.storage_client = storage.Client(project=root_project,credentials=self.credentials)
        self.user_name = user_name
        self.user_id = user_id
        self.project_id = project_id
        self.root_bucket = root_bucket
    
    def generate_download_signed_url_v4(self, blob_name,bucket_name=None):

        bucket = self.storage_client.bucket(self.root_bucket)
        blob = bucket.blob(blob_name)

        url = blob.generate_signed_url(
            version="v4",
            # This URL is valid for 15 minutes
            expiration=datetime.timedelta(minutes=15),
            # Allow GET requests using this URL.
            method="GET",
        )
        return url
    
    def list_buckets(self,prefix=None):
        buckets_ = []
        x = self.storage_client.list_buckets(prefix=prefix)
        for bucket in x:
            buckets_.append(bucket.name)
        return buckets_

    def get_bucket(self,bucket_name=None):
        bucket = self.storage_client.lookup_bucket(self.root_bucket)
        return bucket
    
    def check_blob(self,blob_name,bucket_name=None):
        bucket = self.check_bucket(self.root_bucket)
        blob = bucket.get_blob(blob_name)
        if blob:
            return True
        # self.logger.project_log(f'Checking For Folder {bucket_name}')

    def check_bucket(self,bucket_name=None):
        bucket = self.storage_client.lookup_bucket(self.root_bucket)
        if not bucket:
            return False
        return bucket

    def create_bucket(self,bucket_name=None):
        if not self.check_bucket(self.root_bucket):
            try:
                self.storage_client.create_bucket(self.root_bucket)
                # cloud_logs(f"Created bucket {self.root_bucket}",user_id=self.user_id,project_id=self.project_id)
            except Exception as e:
                raise e
                # cloud_logs(f"Error creating bucket {self.root_bucket}",user_id=self.user_id,project_id=self.project_id,exception=True)

    def create_blob(self,blob_name,bucket_name=None):
        bucket = self.storage_client.lookup_bucket(self.root_bucket)
        blob = bucket.blob(blob_name)
        blob.upload_from_string('')
        # cloud_logs(f"Creating Folder {blob_name} in {self.root_bucket}",user_id=self.user_id,project_id=self.project_id)
            
    def reload_cloud(self,bucket_name=None):
        bucket=self.check_bucket(self.root_bucket)
        if bucket:
            # cloud_logs(f"Reloading {self.root_bucket}",user_id=self.user_id,project_id=self.project_id,exception=True)
            bucket.reload()
    
    def upload_blob(self, source_file_name, destination_blob_name,bucket_name=None):
        """Uploads a file to the bucket."""
        try:
            blob = self.check_blob(self.root_bucket,destination_blob_name)
            if blob:
                blob.upload_from_filename(source_file_name)
                # cloud_logs(f"File {source_file_name} uploaded to {destination_blob_name}.",user_id=self.user_id,project_id=self.project_id)
        except Exception as e:
            raise e
            # cloud_logs(f"could'nt upload file",user_id=self.user_id,project_id=self.project_id,exception=True)
        
    def list_blobs_link(self,bucket_name=None):
        # # Make an authenticated API request
        bucket = self.check_bucket(self.root_bucket)
        blobs_list = {}
        if bucket:
            for i in bucket.list_blobs():
                blobs_list[i.name]=self.generate_download_signed_url_v4(self.root_bucket,i.name)

        return blobs_list
    
    def list_blobss(self,project_name,directory_path,bucket_name=None):
        # # Make an authenticated API request
        bucket = self.storage_client.get_bucket(self.root_bucket)
        blobs_list = []
        regex = f"{self.user_name}/{project_name}/{directory_path}/"
        try:
            for blob in bucket.list_blobs(prefix=self.user_name):
                if (blob.name.startswith(regex)) and not(blob.name.endswith('/')):
                    blobs_list.append(blob.name.split('/')[-1])
                    continue
        except Exception as e:
            raise e
            # cloud_logs(f"Couldn't list files from cloud: {e}",exception=True,user_id=self.user_id,project_id=self.project_id)
        return blobs_list
    
    def download_blob(self, destination_folder,bucket_name=None):
        """Downloads a blob from the bucket."""

        blobs = self.storage_client.list_blobs(self.root_bucket)
        for blob in blobs:
            filename =  blob.name
            destination_file = os.path.join(destination_folder,filename)
            blob.download_to_filename(destination_file)
            file_path = os.path.join(destination_folder,destination_file)
            self.logger.file_logs("File saved {object_name}")
            return file_path
    
    def get_directory(self,project_name,directory_path, download_path,bucket_name=None):
        bucket = self.storage_client.get_bucket(self.root_bucket)
        try:
            for blob in bucket.list_blobs(prefix=self.user_name):
                regex = f"{self.user_name}/{project_name}/{directory_path}/"
                if ((blob.name.startswith(regex)) and not(blob.name.endswith('/'))):
                    filename = blob.name.split("/")[-1]
                    file_path = os.path.join(download_path,filename)
                    with open(file_path,'wb') as f:
                        blob.download_to_file(f) 
            # cloud_logs('File loadeds from Cloud',user_id=self.user_id,project_id=self.project_id)
        except Exception as e:
            raise e
            # cloud_logs('File cannot be loaded Cloud',exception=True,user_id=self.user_id,project_id=self.project_id)   

    def upload_to_cloud(self,project_name,directory_path, dest_blob_folder,dest_bucket_name=None):
        '''Upload files to cloud and remve from local'''
        rel_paths = glob.glob(directory_path + '/**', recursive=True)
        bucket = self.storage_client.bucket(self.root_bucket)
        try:
            for local_file in rel_paths:
                remote_path = f'{self.user_name}/{project_name}/{dest_blob_folder}/{"".join(local_file.split(os.sep)[-1])}'
                if os.path.isfile(local_file):
                    blob = bucket.blob(remote_path)
                    blob.upload_from_filename(local_file)
                    os.remove(local_file)
                    continue
            # cloud_logs("Uploaded files to cloud",user_id=self.user_id,project_id=self.project_id)
        except Exception as e:
            raise e
            # cloud_logs(f"Couldn't upload files to cloud: {e}",exception=True,user_id=self.user_id,project_id=self.project_id)

    def get_user_dir(self,project_name,directory_path,download_path):
        bucket = self.storage_client.get_bucket(self.root_bucket)
        try:
            for blob in bucket.list_blobs():
                if ((blob.name.startswith(directory_path)) and not(blob.name.endswith('/'))):
                    filename = blob.name.split("/")[-1]
                    file_path = os.path.join(download_path,filename)
                    with open(file_path,'wb') as f:
                        blob.download_to_file(f) 
            # cloud_logs('File loadeds from Cloud',user_id=self.user_id,project_id=self.project_id)
        except Exception as e:
            raise e
            # cloud_logs('File cannot be loaded Cloud',exception=True,user_id=self.user_id,project_id=self.project_id)   

