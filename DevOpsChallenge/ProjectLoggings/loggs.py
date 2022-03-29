from datetime import datetime
from DBManagement.mongops import MongoDBmanagement
# ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import uuid

class App_Logger():
    def __init__(self,user_id=None,project_id=None) -> None:
        self.user_id = user_id
        self.project_id = project_id

    @property
    def user_id(self):
        return self._user_id

    @user_id.setter
    def user_id(self, value):
        self._user_id = value
    
    @property
    def project_id(self):
        return self._project_id

    @project_id.setter
    def project_id(self, value):
        self._project_id = value
    
    @staticmethod
    def get_time():
        now = datetime.now()
        date = now.date()
        current_time = now.strftime("%H:%M:%S")
        exec_id = uuid.uuid4()
        return {'date':date,'current_time':current_time,'exec_id':exec_id}

    def cloud_logs(self,log_message,cloud_name='GCP',exception=False,traceback=None):
        if (self.user_id) and (self.project_id):
            mongo=MongoDBmanagement(self.user_id,self.project_id)
            time_ = self.get_time()
            if exception:
                mongo.InsertRecord('CloudData','cloud_exceptions',
                {'user_id':self.user_id,'project_id':self.project_id,'message':log_message,
                'date':str(time_['date']),'time':str(time_['current_time']),'exec_id':str(time_['exec_id']),'traceback':self.tracebacks(traceback)})
            else:
                mongo.InsertRecord('CloudData','cloud_logs',
                {'user_id':self.user_id,'project_id':self.project_id,'message':log_message,
                'date':str(time_['date']),'time':str(time_['current_time']),'exec_id':str(time_['exec_id'])})

    @staticmethod
    def tracebacks(traceback):
        try:
            exception_type, exception_object, exception_traceback = traceback
            filename = exception_traceback.tb_frame.f_code.co_filename
            line_number = exception_traceback.tb_lineno
            return {'exception_type':str(exception_type),'filename':str(filename),'line_no':str(line_number),}
        except Exception as e:
            return None

    def project_logs(self,log_message,traceback = None,exception=False):
        if (self.user_id) and (self.project_id):
            mongo=MongoDBmanagement(self.user_id,self.project_id)
            time_ = self.get_time()
            if exception:
                if traceback:
                    mongo.InsertRecord('ProjectData','project_exceptions',
                    {'user_id':self.user_id,'project_id':self.project_id,'message':log_message,
                    'date':str(time_['date']),'time':str(time_['current_time']),'exec_id':str(time_['exec_id']),'traceback':self.tracebacks(traceback)})
            else:
                mongo.InsertRecord('ProjectData','project_logs',
                {'user_id':self.user_id,'project_id':self.project_id,'message':log_message,
                'date':str(time_['date']),'time':str(time_['current_time']),'exec_id':str(time_['exec_id'])})
        

    def user_logs(self,log_message,exception=False,traceback=None):
        if (self.user_id):
            mongo=MongoDBmanagement(self.user_id)
            time_ = self.get_time()
            if exception:
                mongo.InsertRecord('UsersData','user_exceptions',
                {'user_id':self.user_id,'message':log_message,
                'date':str(time_['date']),'time':str(time_['current_time']),'exec_id':str(time_['exec_id']),'traceback':self.tracebacks(traceback)})
            else:
                mongo.InsertRecord('UsersData','user_logs',
                {'user_id':self.user_id,'message':log_message,
                'date':str(time_['date']),'time':str(time_['current_time']),'exec_id':str(time_['exec_id'])})

    def request_logs(self,log_message,exception=False,traceback=None):
        if self.user_id:
            mongo=MongoDBmanagement(self.user_id)
            time_ = self.get_time()
            if exception:
                mongo.InsertRecord('UsersData','request_exceptions',
                {'user_id':self.user_id,'message':log_message,
                'date':str(time_['date']),'time':str(time_['current_time']),'exec_id':str(time_['exec_id']),'traceback':self.tracebacks(traceback)})
            else:
                mongo.InsertRecord('UsersData','request_logs',
                {'user_id':self.user_id,'message':log_message,
                'date':str(time_['date']),'time':str(time_['current_time']),'exec_id':str(time_['exec_id'])})
