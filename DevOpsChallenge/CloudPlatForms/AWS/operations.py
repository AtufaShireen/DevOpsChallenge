import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
load_dotenv()
import os



import glob
class AWSOps():
    def __init__(self,user_name,user_id,project_id=None,root_bucket='automlops'):
        ACCESS_KEY = str(os.environ.get('AWS_ACCESS_KEY'))
        SECRET_KEY = str(os.environ.get('AWS_SECRET_KEY'))  
        region_name = 'us-east-1'
        self.s3_client = boto3.client('s3',aws_access_key_id=ACCESS_KEY,aws_secret_access_key=SECRET_KEY,region_name=region_name)
        session = boto3.Session(aws_access_key_id=ACCESS_KEY,aws_secret_access_key=SECRET_KEY)
        self.resource = session.resource('s3')
        self.user_id = user_id
        self.user_name=user_name
        self.project_id = project_id
        self.root_bucket = root_bucket
        
    def get_bucket(self,bucket_name=None):
        bucket = self.resource.Bucket(self.root_bucket)
        return bucket
    
    def check_bucket(self,bucket_name=None):
        bucket = self.resource.Bucket(self.root_bucket)
        if bucket.creation_date:
            return True
        else:
            return False

    def create_bucket(self,bucket_name=None):
        """Create an S3 bucket in default region"""
        # Create bucket
        try:
            self.resource.create_bucket(Bucket=self.root_bucket)

        except Exception as e:
            # App_Logger.cloud_logs(f"Error creating bucket {bucket_name}",cloud_name='AWS',exception=True,user_id=self.user_id,project_id=self.project_id)
            return False
        return True

    def create_blob(self,folder_name,bucket_name=None):
        try:
            self.s3_client.put_object(Bucket=self.root_bucket,Key=folder_name)
        except Exception as e:
            return False

    def check_blob(self,blob_name,bucket_name=None):
        blobs = self.s3_client.list_objects(Bucket = self.root_bucket,Prefix = blob_name)['Contents']
  
        if blobs:
            return True

    def list_buckets(self,prefix=None):
        response = self.s3_client.list_buckets(prefix=prefix)
        list_=[]
        for bucket in response['Buckets']:
            list_.append(bucket['Name'])
        return list_

    def list_blobs_link(self,bucket_name=None):
        objects = self.s3_client.list_objects(Bucket = self.root_bucket)
        blobs_list = {}
        for obj in objects:
            blobs_list[obj['Key']]=self.down_blob_url(self.root_bucket,obj['Key'])
        return blobs_list
    
    def list_blobss(self,project_name,directory_path,bucket_name=None):
        blobs = self.s3_client.list_objects(Bucket = self.root_bucket,Prefix = self.user_name)['Contents']
        blobs_list = []
        regex = f"{self.user_name}/{project_name}/{directory_path}/"
        try:
            for blob in blobs:
                if (blob['Key'].startswith(regex)) and not(blob['Key'].endswith('/')):
                    blobs_list.append(blob['Key'].split('/')[-1])
        except Exception as e:
            pass
            raise e
            # App_Logger.cloud_logs(f"Couldnt list files from folder:{e}",cloud_name='AWS',user_id=self.user_id,project_id=self.project_id,exception=True)
        return blobs_list

    def get_directory(self,project_name,directory_path, download_path,bucket_name=None):
        bucket = self.resource.Bucket(self.root_bucket)
        regex = f'{self.user_name}/{project_name}/{directory_path}'
        try:
            for s3_key in self.s3_client.list_objects(Bucket=self.root_bucket, Prefix=self.user_name)['Contents']:
                s3_object = s3_key['Key']
                if (not(s3_object.endswith('/')) and (s3_object.startswith(regex))):
                    filename = (s3_object).split('/')[-1]
                    file_path = os.path.join(download_path,filename)
                    bucket.download_file(s3_object,file_path)
            # App_Logger.cloud_logs('File loadeds from Cloud',cloud_name='AWS',user_id=self.user_id,project_id=self.project_id)
        except Exception as e:
            raise e
            # App_Logger.cloud_logs('File cannot be loaded Cloud',exception=True,cloud_name='AWS',user_id=self.user_id,project_id=self.project_id) 


    def generate_download_signed_url_v4(self, blob_name,bucket_name=None, expiration=3600):
        """Generate a presigned URL to share an S3 object"""
        try:
            response = self.s3_client.generate_presigned_url('get_object',
                                                        Params={'Bucket': self.root_bucket,
                                                                'Key': blob_name},
                                                        ExpiresIn=expiration)
        except ClientError as e:
            # App_Logger.cloud_logs(f"Error getting link bucket {self.root_bucket}",cloud_name='AWS',exception=True,user_id=self.user_id,project_id=self.project_id)
            return None
        return response
    
    def upload_to_cloud(self,project_name,directory_path, dest_blob_folder, dest_bucket_name=None):
        '''Upload files to cloud and remve from local'''
        rel_paths = glob.glob(directory_path + '/**', recursive=True)
        
        bucket = self.root_bucket
        try:
            for local_file in rel_paths:
                remote_path = f'{self.user_name}/{project_name}/{dest_blob_folder}/{"".join(local_file.split(os.sep)[-1])}'
                if os.path.isfile(local_file):
                    self.s3_client.upload_file(local_file,bucket,remote_path)
                    os.remove(local_file)
            # App_Logger.cloud_logs('File uploaded to Cloud',cloud_name='AWS',user_id=self.user_id,project_id=self.project_id)
        except Exception as e:
            raise e
            # App_Logger.cloud_logs(f"Couldn't upload files to cloud: {e}",exception=True,cloud_name='AWS',user_id=self.user_id,project_id=self.project_id)

# class ReadAWSOps():
#     def __init__(self,user_id,project_id,access_key,secret_key):
#         ACCESS_KEY = access_key
#         SECRET_KEY = secret_key
#         self.s3_client = boto3.client('s3',aws_access_key_id=ACCESS_KEY,aws_secret_access_key=SECRET_KEY)
#         session = boto3.Session(aws_access_key_id=ACCESS_KEY,aws_secret_access_key=SECRET_KEY)
#         self.resource = session.resource('s3')
#         self.user_id = user_id
#         self.project_id = project_id
    
#     def get_user_directory(self,directory_path,bucket_name,download_path):
#         bucket = self.resource.Bucket(bucket_name)
#         try:
#             for s3_key in self.s3_client.list_objects(Bucket=bucket_name)['Contents']:
#                 s3_object = s3_key['Key']
#                 if (not(s3_object.endswith('/')) and (s3_object.startswith(directory_path))):
#                     filename = (s3_object).split('/')[-1]
#                     file_path = os.path.join(download_path,filename)
#                     bucket.download_file(s3_object,file_path)
#             user_logs('Retrieved files from AWS',user_id = self.user_id)
#         except Exception as e:
#             user_logs('Could not retrieve files from AWS',user_id = self.user_id,exception=True)
# gcp = AWSOps('sfd','fgh','dfg')
# print(gcp.list_buckets(),'connected')
# # bucket = gcp.get_bucket('atufa')
# blobs = gcp.s3_client.list_objects(Bucket='automlops')
# for i in blobs['Contents']:
#     print(i['Key'] )