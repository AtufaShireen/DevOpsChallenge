from pickle import TRUE
import sys
from dotenv import load_dotenv
load_dotenv()
import logging
# from wsgiref import simple_server
import json
from flask import Flask, request, render_template,redirect,url_for,session,flash,Response,jsonify
from functools import wraps
from flask_cors import CORS, cross_origin
# import flask_monitoringdashboard as dashboard
import os,uuid,bcrypt
from datetime import datetime
from ProjectLoggings.loggs import App_Logger
from DBManagement.mongops import MongoDBmanagement
from DBManagement.bqops import BigQueryManagement
from CloudPlatForms.GCP.operations import GCPOps
from CloudPlatForms.AWS.operations import AWSOps
from ValidationProcess.insertion_validation import InsertPreprocess
from automl.models import getclassification,getregression
from forms import ProjectConfigForm,CustomerSegmentForm
from customerpersonna.analysis import SegmentAnalysis,Segmentation
import pandas as pd
from joblib import load,dump
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, JobExecutionEvent,EVENT_ALL
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from flask_mail import Mail,Message
from werkzeug.utils import secure_filename
os.putenv('LANG', 'en_US.UTF-8')
os.putenv('LC_ALL', 'en_US.UTF-8')

logging.basicConfig(level=logging.info)
app = Flask(__name__)
app.config['SECRET_KEY']=os.environ.get('SECRET_KEY','1234')
import shutil
# app.config['EXPLAIN_TEMPLATE_LOADING'] = True
# root_dir= os.path.dirname(app.root_path)
root_dir = app.root_path
logging.info(f'*ROOT DIR: {root_dir}')
app.config['DEBUG'] = True
app.config['FLASK_ENV'] = 'development'
# app.config['TESTING'] = True
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME',None) 
app.config['FLASK_ENV'] = 'development'
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD',None)
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False

# dashboard.config.init_from(file=f'{app.instance_path}\config.cfg')
# dashboard.bind(app)
CORS(app)
mail=Mail(app)
scheduler = BackgroundScheduler({
    'apscheduler.executors.default': {
        'class': 'apscheduler.executors.pool:ThreadPoolExecutor',
        'max_workers': '20'
    },
    'apscheduler.executors.processpool': {
        'type': 'processpool',
        'max_workers': '5'
    },
    'apscheduler.job_defaults.coalesce': 'false',
    'apscheduler.job_defaults.max_instances': '3',
    'apscheduler.timezone': 'UTC',
})
scheduler.start()

def my_listener(event):

    if event.exception:
        logging.info('The validation processed has crashed please check logs :(')
    else:
        logging.info('The validation processed has worked  please check logs:)')

scheduler.add_listener(my_listener, EVENT_JOB_ERROR|EVENT_JOB_EXECUTED)

def get_user_id():
    return '134'
# dashboard.config.group_by= get_user_id
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kws):
            if ('email' in session) and ('user_id' in session):
                return f(*args, **kws) 
            else:
                flash("Thee shall not pass without login!")
                return redirect(url_for('login'))           
    return decorated_function

#@cross_origin()
def ids_required(f):
    @wraps(f)
    def decorated_function(*args, **kws):
            if 'project_id' in session:
                return f(*args, **kws)            
    return decorated_function
    
# @app.before_request
# def before_request():
#     if (request.endpoint != 'login') and (request.endpoint != 'register') and (request.endpoint != 'index'):
#         user_id = str(session['user_id'])
#         log_writer = App_Logger(user_id)
#         try:
#             log_writer.user_logs(f"{str(request.remote_addr)}, {str(request.method)}, {str(request.scheme)}, {str(request.full_path)}, ")
#         except Exception as e:
            # log_writer.user_logs(f"{str(request.remote_addr)}, {str(request.method)}, {str(request.scheme)}, {str(request.full_path)}, ",exception=True,traceback = sys.exc_info())

def create_project_bucket(cloud,user_id,project_id):
    '''Creates bucket for project if not already exists'''
    logging.info("Creating Project Bucket")
    print(cloud,project_id,user_id)
    mongo = MongoDBmanagement(user_id=user_id,project_id=project_id)
    logger = App_Logger(user_id,project_id)
    project_name = mongo.findfirstRecord('ProjectData','projects',{'project_id':project_id}).get('project_title')
    user = mongo.findfirstRecord('UsersData','registered_users',{'user_id':user_id})
    user_name = user.get('user_name')
    
    if cloud=='AWS':
        portal = AWSOps(user_id=user_id,user_name=user_name,project_id=project_id)
    elif cloud == 'GCP':
        portal = GCPOps(user_name=user_name)
    
    root = f'{user_name}/{project_name}'
    folder_check = [f'{root}/',f'{root}/train-batch-files/',f'{root}/predict-batch-files/',
    f'{root}/train-batch-models/',f'{root}/train-bad-archive-data/',f'{root}/train-good-archive-data/',
    f'{root}/train-files/',f'{root}/prediction-files/',f'{root}/predict-bad-archive-data/',
    f'{root}/predict-good-archive-data/',f'{root}/preprocess-pipe/',f'{root}/metrics/']
    try:
        for f in folder_check:
            portal.create_blob(f)
        with app.app_context():
            logger.project_logs("Project successfully initiated")
            logging.info("Project successfully initiated")
            # send_mail(reciever= user.get('email'),body="Project successfully initiated")
        return True
    except Exception as e:
        with app.app_context():
            logger.project_logs(f"Project cannot be created on cloud {e}",exception=True,traceback = sys.exc_info())
            logging.info("Project error")
            # send_mail(reciever= user.get('email'),body="Project cannot be created on cloud, error: {e}")
        print('e-',e)
        raise e
        return False

def send_mail(body,reciever):
    print(app.config['MAIL_USERNAME']  )
    msg = Message(subject='AutoNeuro Update By Atufa',sender=app.config['MAIL_USERNAME'],
    reply_to=reciever,cc=['atufashireen@gmail.com'],recipients=['ruqiyanishath@gmail.com'])
    msg.body = body
    mail.send(msg)    

@app.route("/login", methods=["POST", "GET"])
def login():
    if "email" in session:
        flash("Already logged in")
        return redirect(url_for("dashboard"))
    
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        mongo = MongoDBmanagement()
        registered_found = mongo.findfirstRecord(db_name='UsersData',collection_name='registered_users',query={"email": email})
        if not registered_found:
            flash("PLease register First!")
        email_found = mongo.findfirstRecord(db_name='UsersData',collection_name='allowed_users',query={"email": email})
        
        if email_found:
            email_val = email_found['email']
            passwordcheck = registered_found['password']
            
            if bcrypt.checkpw(password.encode('utf-8'), passwordcheck):
                session["email"] = email_val
                session["user_id"] = registered_found['user_id']
                flash("You're already logged in")
                # log_writer.user_logs(f"Logged in ")
                return redirect(url_for('dashboard',user_id=session['user_id']))
            else:
                flash('Wrong password')
                return redirect(url_for('login'))
        else:
            flash('Email not found')
            return redirect('login')
    return render_template('login.html')

@app.route("/register", methods=['POST', 'GET'])
def register():
    mongo = MongoDBmanagement()
    if "email" in session:
        flash("Already registered")
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        user = request.form.get("fullname")
        email = request.form.get("email")
        
        password1 = request.form.get("password1")
        password2 = request.form.get("password2")
        
        user_allowed = mongo.findfirstRecord(db_name='UsersData',collection_name='allowed_users',query={"name": user,"email":email})
        if not user_allowed:
            user_found = mongo.findfirstRecord(db_name='UsersData',collection_name='registered_users',query={"name": user})
            email_found = mongo.findfirstRecord(db_name='UsersData',collection_name='registered_users',query={"email": email})
            
            if user_found:
                flash('That username is taken')
                return redirect(url_for('register'))
            if email_found:
                flash('This email is taken login instead')
                return redirect(url_for('register'))
            if password1 != password2:
                flash('Passwords should match!')
                return redirect(url_for('register'))
            else:
                hashed = bcrypt.hashpw(password2.encode('utf-8'), bcrypt.gensalt())
                user_id = str(uuid.uuid4())
                user_input = {'user_name': user, 'email': email, 'password': hashed,'user_id':user_id}
                mongo.InsertRecord(db_name='UsersData',collection_name='registered_users',record=user_input)
                flash("registered successfully")
                flash("Please contact admin(atufashireen@gmail.com) to use our services") 
                return redirect(url_for('project_board',user_id=user_id))
        else:
            flash("Please contact admin(atufashireen@gmail.com) to use our services") 
    print('heere=')
    return render_template('register.html')

@app.route("/userdashboard/", methods=['GET'])
@cross_origin()
@login_required
def dashboard(user_id=None):
    user_id = session['user_id']
    # send_mail(body=f'Hi from shireen',reciever = 'atufashireen@gmail.com')
    
    return redirect(url_for('project_board'))
    # return render_template('dashboard.html')

def validate_insert_train(user_id,project_id,folder_path,user_root,type):
    '''Recieve Train and Predict folder, validate and create hdf store in warehouse'''
    logging.info("Validating Inserts")
    mongo=MongoDBmanagement(user_id=user_id,project_id=project_id)
    logger = App_Logger(user_id,project_id)
    project = mongo.findfirstRecord('ProjectData','projects',{'project_id':project_id})
    user = mongo.findfirstRecord('UsersData','registered_users',{'user_id':user_id})
    user_name = user.get('user_name')
    cloud = project.get('cloud')
    project_name = project.get('project_title')

    raw_folder = folder_path
    try:
        validate = InsertPreprocess(path=raw_folder,user_id=user_id,project_id=project_id,user_root=user_root,type=type)
        mongo.updateOneRecord('ProjectData','project_details',query={'$set':{'train_tag':'progress','last_update':str(datetime.now())}},prev={'project_id':project_id})
        
        process = validate.process_validation()
        if process['status'] == True:
            with app.app_context():
                # send_mail(body=f'Project: {project_name} Training Files evaluated will be uploaded to cloud',reciever = user.get('email'))
                mongo.updateOneRecord('ProjectData','project_details',query={'$set':{'train_tag':'validated','last_update':str(datetime.now())}},prev={'project_id':project_id})
        
                logger.project_logs(f'Project: {project_name} Training Files evaluated will be uploaded to cloud')
                logging.info("Project Training Files evaluated will be uploaded to cloud")
        else:
            with app.app_context():
                shutil.rmtree(folder_path,ignore_errors =True)
                logging.info('Removed raw dir')
                logger.project_logs(f'Files couldnt be evaluated: {process["message"]}',exception=True,traceback = sys.exc_info())
                # send_mail(body=f'Project: {project_name} Files couldnt be evaluated,error : {process["message"]}',reciever = user.get('email'))
                logging.info("Files couldnt be evaluated:")
                mongo.updateOneRecord('ProjectData','project_details',query={'$set':{'train_tag':'failed','last_update':str(datetime.now())}},prev={'project_id':project_id})
        
    except Exception as e:
        
        with app.app_context():
            shutil.rmtree(folder_path,ignore_errors =True)
            logging.info('Removed raw dir')
            # send_mail(body=f'Project: {project_name} Files couldnt be evaluated,error: {e}',reciever = user.get('email'))
            logger.project_logs(f'Files couldnt be evaluated: {e}',exception=True,traceback = sys.exc_info())
            logging.info("Files couldnt be evaluated:")
        print(e)
        raise e
    try:
        final_folder = os.path.join(user_root,'FINALDATA',user_id,project_id)
        bad_folder = os.path.join(user_root,'BADRAWDATA',user_id,project_id)
        good_folder = os.path.join(user_root,'GOODRAWDATA',user_id,project_id)

        if os.getenv('cloud_env')=='True':
            if cloud=='AWS':
                portal = AWSOps(user_id=user_id,user_name=user_name,project_id=project_id)
            elif cloud == 'GCP':
                portal = GCPOps(user_name=user_name)
            portal.upload_to_cloud(project_name=project_name,directory_path=raw_folder,dest_blob_folder=f'train-batch-files')
            portal.upload_to_cloud(project_name=project_name,directory_path=final_folder,dest_blob_folder=f'train-files')
            portal.upload_to_cloud(project_name=project_name,directory_path=bad_folder,dest_blob_folder=f'train-bad-archive-data')
            portal.upload_to_cloud(project_name=project_name,directory_path=good_folder,dest_blob_folder=f'train-good-archive-data')
        
        with app.app_context():
            # send_mail(body=f'Project: {project_name} Training Files validated Successfully',reciever= user.get('email'))
            logger.project_logs('Project evaluated succesfully')
            logging.info("Project evaluated succesfully")
            
    except Exception as e:
        with app.app_context():
            # send_mail(body=f'Project: {project_name} Evaluated Taining Files cannot be uploaded to cloud',reciever = user.get('email'))
            logger.project_logs(f'Project: {project_name} Evaluated Training Files cannot be uploaded to cloud {e}',exception=True,traceback = sys.exc_info())
            logging.info(" Evaluated Training Files cannot be uploaded to cloud")
        print(e)
        raise e


def validate_insert_predict(user_id,project_id,folder_path,user_root,type):
    '''Recieve Train and Predict folder, validate and create hdf store in warehouse'''
    logging.info("Validating Inserts")
    mongo=MongoDBmanagement(user_id=user_id,project_id=project_id)
    logger = App_Logger(user_id,project_id)
    project = mongo.findfirstRecord('ProjectData','projects',{'project_id':project_id})
    user = mongo.findfirstRecord('UsersData','registered_users',{'user_id':user_id})
    user_name = user.get('user_name')
    cloud = project.get('cloud')
    project_name = project.get('project_title')
    raw_folder = folder_path
    try:
        validate = InsertPreprocess(path=raw_folder,user_id=user_id,project_id=project_id,user_root=user_root,type=type)
        mongo.updateOneRecord('ProjectData','project_details',query={'$set':{'train_tag':'progress','last_update':str(datetime.now())}},prev={'project_id':project_id})
        
        process = validate.process_validation()
        if process['status'] == True:
            with app.app_context():
                # send_mail(body=f'Project: {project_name} Predtion Files evaluated will be uploaded to cloud',reciever = user.get('email'))
                logger.project_logs(f'Project: {project_name} Predtion Files evaluated will be uploaded to cloud')
        else:
            with app.app_context():
                shutil.rmtree(folder_path,ignore_errors =True)
                logging.info('Removed raw dir')
                # send_mail(body=f'Project: {project_name} Files couldnt be evaluated, error {e}',reciever = user.get('email'))
                logger.project_logs(f'Files couldnt be evaluated: {process["message"]}',exception=True,traceback = sys.exc_info())
        
    except Exception as e:
        with app.app_context():
            shutil.rmtree(folder_path,ignore_errors =True)
            logging.info('Removed raw dir')
            # send_mail(body=f'Project: {project_name} Files couldnt be evaluated, error {e}',reciever = user.get('email'))
            logger.project_logs(f'Files couldnt be evaluated: {e}',exception=True,traceback = sys.exc_info())
        print(e)
        raise e
    try:
        final_folder = os.path.join(user_root,'FINALDATA',user_id,project_id)
        bad_folder = os.path.join(user_root,'BADRAWDATA',user_id,project_id)
        good_folder = os.path.join(user_root,'GOODRAWDATA',user_id,project_id)
        if os.getenv('cloud_env')=='True':
            if cloud=='AWS':
                portal = AWSOps(user_id=user_id,user_name=user_name,project_id=project_id)
            elif cloud == 'GCP':
                portal = GCPOps(user_name=user_name)
            portal.upload_to_cloud(project_name=project_name,directory_path=raw_folder,dest_blob_folder=f'predict-batch-files')
            portal.upload_to_cloud(project_name=project_name,directory_path=final_folder,dest_blob_folder=f'predict-files')
            portal.upload_to_cloud(project_name=project_name,directory_path=bad_folder,dest_blob_folder=f'predict-bad-archive-data')
            portal.upload_to_cloud(project_name=project_name,directory_path=good_folder,dest_blob_folder=f'predict-good-archive-data')
        
        with app.app_context():
            # send_mail(body=f'Project: {project_name} Prediction Files validated Successfully',reciever= user.get('email'))
            logger.project_logs('Project evaluated succesfully')

            mongo.updateOneRecord('ProjectData','project_details',query={'$set':{'predict_tag':'validated','last_update':str(datetime.now())}},prev={'project_id':project_id})
        
    except Exception as e:
        with app.app_context():
            # send_mail(body=f'Project: {project_name} Evaluated Taining Files cannot be uploaded to cloud',reciever = user.get('email'))
            logger.project_logs(f'Project: {project_name} Evaluated Predtion Files cannot be uploaded to cloud {e}',exception=True,traceback = sys.exc_info())
        print(e)
        raise e

@app.route('/add_batch_files/<project_id>',methods=['POST','GET'])
def add_batch_files(project_id):
    user_id = session['user_id']
    print('called!')
    if request.method=='POST':
        print('yes')
        train_root = os.path.join(root_dir,'ValidationProcess','TRAIN')
        train_folder = os.path.join(train_root,'RAWDATA',user_id,project_id)
        if not os.path.isdir(train_folder):
            os.makedirs(train_folder,exist_ok=True)
        train_files = request.files.getlist('trainfile[]')
        files = [secure_filename(file.filename) for file in train_files if file.filename!='']
        if files:
            print('====================-=-=',files)
            for file_num in range(len(train_files)):
                filename = os.path.join(train_folder,files[file_num])
                train_files[file_num].save(filename)
                print("saved",filename)
            job = scheduler.add_job(validate_insert_train,
        kwargs={'user_id':user_id,'project_id':project_id,'folder_path':train_folder,
        'type':'train','user_root':train_root})
        predict_root = os.path.join(root_dir,'ValidationProcess','PREDICT')
        predict_folder = os.path.join(predict_root,'RAWDATA',user_id,project_id)
        if not os.path.isdir(predict_folder):
            os.makedirs(predict_folder,exist_ok=True)
        predict_files = request.files.getlist('predictfile[]')
        files = [secure_filename(file.filename) for file in predict_files if file.filename!='']
        if files:
            print('====================-=-=',files)
            for file_num in range(len(predict_files)):
                filename = os.path.join(predict_folder,files[file_num])
                predict_files[file_num].save(filename)
                print("saved",filename)
            job = scheduler.add_job(validate_insert_predict,
            kwargs={'user_id':user_id,'project_id':project_id,'folder_path':predict_folder,
            'type':'predict','user_root':predict_root})
        
        flash("files have been recieved, they wll be uploaded to cloud after validation!")
        return redirect(url_for('project_board'))
    return redirect(url_for('config_project'))

@app.route("/config_project/<project_id>",methods=['POST','GET'])
def config_project(project_id):
    user_id = session['user_id']
    mongo=MongoDBmanagement(user_id=user_id,project_id=project_id)
    project = mongo.findfirstRecord('ProjectData','projects',{'project_id':project_id})
    if project.get('mltype')=='customersegmentation':
        return render_template('configure_seg_proj.html',project=project)    
    return render_template('configure_proj.html',project=project)

@app.route("/project_board", methods=['GET'])
@cross_origin()
@login_required
def project_board(user_id=None):
    mongo = MongoDBmanagement()
    user_id = session['user_id']
    projects = mongo.findRecordOnQuery('ProjectData','projects',{'user_id':user_id})
    return render_template('project_board.html',user_proj=projects) #make check

@app.route('/file_link/<project_id>/<directory_path>/<blob_name>',methods=['GET'])
@login_required
@cross_origin()
def file_link(project_id,directory_path,blob_name):
    user_id = session['user_id']
    mongo = MongoDBmanagement(user_id,project_id)
    logger = App_Logger(user_id,project_id)
    project = mongo.findfirstRecord('ProjectData','projects',{'project_id':project_id})
    project_name = project.get('project_title')
    portal=project.get('cloud')
    user_name = mongo.findfirstRecord('UsersData','registered_users',{'user_id':user_id}).get('user_name')
    if portal == 'AWS':
        clouds = AWSOps(user_id=user_id,project_id=project.get('project_id'),user_name=user_name)
    elif portal == 'Azure':
        pass
    else:
        clouds = GCPOps(user_name=user_name)
    try:
        blob_link = f'{user_name}/{project_name}/{directory_path}/{blob_name}'
        return clouds.generate_download_signed_url_v4(blob_name=blob_link) 
    except Exception as e:
        logger.project_logs(f'file link cannot retrieved {e}',exception=True,traceback = sys.exc_info())
        print('--e',e)
        raise e
        
    return None
    
@app.route("/file_board/<string:project_id>", methods=['GET','POST'])
@login_required
@cross_origin()
def files_board(project_id):
    user_id = session['user_id']
    mongo = MongoDBmanagement(user_id=user_id,project_id=project_id)
    project = mongo.findfirstRecord('ProjectData','projects',{'project_id':project_id})
    user_name = mongo.findfirstRecord('UsersData','registered_users',{'user_id':user_id}).get('user_name')
    
    portal =project.get('cloud')
    project_name = project.get('project_title')
    folders = {}
    if portal == 'AWS':
        clouds = AWSOps(user_id=user_id,project_id=project_id,user_name=user_name)
    elif portal == 'Azure':
        pass
    else:
        clouds = GCPOps(user_name=user_name)
    print('---------------------important ghanit-------',user_name,project_name)
    x = clouds.check_blob(blob_name=f'{user_name}/{project_name}/')
    print('---------------------x',x)
    if not x:
        flash('project doesnot exists in cloud')
        return redirect(url_for('add_project'))
    folder_check = ['train-batch-files','predict-batch-files','train-batch-models','preprocess-pipe',
    'train-bad-archive-data','train-good-archive-data','prediction-files','train-files',
    'predict-bad-archive-data','predict-good-archive-data','metrics-folder']
    for f in folder_check:
        files = clouds.list_blobss(project_name=project_name,directory_path=f)
        folders[f] = files
    return render_template('file_management.html',folders = folders,project=project)

@app.route('/add_project',methods=['GET','POST'])
@login_required
@cross_origin()
def add_project(user_id=None):
    form = ProjectConfigForm()
    user_id = session['user_id']  

    if request.method =='POST':
        if form.validate_on_submit():
            record = {
                'project_id':str(uuid.uuid4()),
                'user_id': user_id,
                'project_title':request.form.get('project_title'),
                'project_desc' : request.form.get('project_desc'),
                'file_regex' : request.form.get('file_regex'),
                'train_schema' : request.form.get('train_schema'),
                'test_schema' : request.form.get('test_schema'),
                'mltype' : request.form.get('mltype'),
                'cloud': request.form.get('cloud'),

            }
            try:
                mongo = MongoDBmanagement(user_id=user_id,project_id=record['project_id'])
                logger = App_Logger(user_id,record['project_id'])
                proj =mongo.findfirstRecord('ProjectData','projects',{'project_title':record['project_title']})
                if not proj:
                    mongo.InsertRecord('ProjectData','projects',record)
                    try:
                        logger.user_logs(log_message = 'New project added successfully')
                        logger.project_logs(log_message='created bucket for project')
                        flash('New project added successfully')
                        mongo.InsertRecord('ProjectData','project_details',
                        {'user_id':user_id,'project_id':record['project_id'],'project_title':record['project_title'],
                        'train_tag':'arrived','predict_tag':'arrived',
                        'last_update':datetime.now(),'metrics':{},'mltype':record['mltype'],'train_failures':0,'train_successes':0}
                        )
                        if os.getenv('cloud_env')=='True':
                            print('-------------------------------------cloud')
                            scheduler.add_job(create_project_bucket,kwargs = {'cloud':request.form.get('cloud'),'project_id':record['project_id'],'user_id':record['user_id']})
                        
                        return redirect(url_for('project_board'))
                    except Exception as e:
                        flash('Project couldnt be added to cloud')
                        mongo.deleteRecord('ProjectData','projects',{'project_id':record['project_id']})
                        logger.user_logs(log_message=f'project couldnt be added to bucket: {e}',exception=True,traceback = sys.exc_info())
                        print('--e',e)
                        raise e
                else:
                    flash('Project names should be unique')
            except Exception as e:
                logger.user_logs(log_message=f'project couldnt be added: {e}',exception=True,traceback = sys.exc_info())
                print('--e',e)
                raise e

    return render_template('add_project.html',form=form)

@app.route('/add_cust_project',methods=['GET','POST'])
def add_cust_project(user_id=None):
    form = CustomerSegmentForm()
    user_id = session['user_id'] 

    if request.method =='POST':
        if form.validate_on_submit():
            record = {
                'project_id':str(uuid.uuid4()),
                'user_id': user_id,
                'project_title':request.form.get('project_title'),
                'project_desc' : request.form.get('project_desc'),
                'file_regex' : request.form.get('file_regex'),
                'train_schema' : request.form.get('column_schema'),
                'mltype' : "customersegmentation",
                'cloud': request.form.get('cloud'),
            }
            try:
                mongo = MongoDBmanagement(user_id=user_id,project_id=record['project_id'])
                logger = App_Logger(user_id,record['project_id'])
                proj =mongo.findfirstRecord('ProjectData','projects',{'project_title':record['project_title']})
                if not proj:
                    mongo.InsertRecord('ProjectData','projects',record)
                    try:
                        logger.user_logs(log_message = 'New project added successfully')
                        logger.project_logs(log_message='created bucket for project')
                        flash('New project added successfully')
                        mongo.InsertRecord('ProjectData','project_details',
                        {'user_id':user_id,'project_id':record['project_id'],'project_title':record['project_title'],
                        'train_tag':'arrived','predict_tag':'arrived',
                        'last_update':datetime.now(),'metrics':{},'mltype':record['mltype'],'train_failures':0,'train_successes':0}
                        )
                        if os.getenv('cloud_env')=='True':
                            print('-------------------------------------cloud')
                            scheduler.add_job(create_project_bucket,kwargs = {'cloud':request.form.get('cloud'),'project_id':record['project_id'],'user_id':record['user_id']})
                        
                        return redirect(url_for('project_board'))
                    except Exception as e:
                        flash('Project couldnt be added to cloud')
                        mongo.deleteRecord('ProjectData','projects',{'project_id':record['project_id']})
                        logger.user_logs(log_message=f'project couldnt be added to bucket: {e}',exception=True,traceback = sys.exc_info())
                        print('--e',e)
                        raise e
                else:
                    flash('Project names should be unique')
            except Exception as e:
                logger.user_logs(log_message=f'project couldnt be added: {e}',exception=True,traceback = sys.exc_info())
                print('--e',e)
                raise e
            return redirect(url_for('project_board'))
    return render_template('add_cust_proj.html',form=form)

@app.route('/')
@cross_origin()
def index():
    return render_template('index.html')

@app.route("/project_board/project_view/<string:project_id>", methods=['GET','POST'])
@login_required
@cross_origin()
def project_view(project_id):
    user_id = session['user_id']
    mongo = MongoDBmanagement(user_id,project_id)
    proj = mongo.findfirstRecord('ProjectData','projects',{'project_id':project_id})
    
    return render_template("project_view.html",proj=proj)

@app.route("/project_board/project_view/<string:project_id>/logs", methods=['GET','POST'])
@cross_origin()
def project_log_report(project_id):
    user_id = session['user_id']
    mongo = MongoDBmanagement(user_id,project_id)
    proj_logs = mongo.findRecordOnQuery('ProjectData','project_logs',{'project_id':project_id})
    
    proj = mongo.findfirstRecord('ProjectData','projects',{'project_id':project_id})
    if proj_logs:
        return render_template('project_log_report.html',proj_logs=proj_logs,proj=proj)
    else:
        return render_template('project_log_report.html',proj_logs=[],proj=proj)

@app.route("/project_board/project_view/<string:project_id>/exception_logs", methods=['GET','POST'])
@cross_origin()
def project_log_exception_report(project_id):
    user_id = session['user_id']
    mongo = MongoDBmanagement(user_id,project_id)
    
    proj = mongo.findfirstRecord('ProjectData','projects',{'project_id':project_id})
    proj_exception_logs = mongo.findRecordOnQuery('ProjectData','project_exceptions',{'project_id':project_id})
    print('--------------------sdfgh--------------')
    if proj_exception_logs:
        return render_template('project_exception_log_report.html',proj_logs = proj_exception_logs,proj=proj)
    else:
        return render_template('project_exception_log_report.html',proj_logs = [],proj=proj)

@app.route("/project_board/project_view/<string:project_id>/project_report", methods=['GET','POST'])
@cross_origin()
def project_report(project_id):
    user_id = session['user_id']
    mongo = MongoDBmanagement(user_id,project_id)
    
    proj = mongo.findfirstRecord('ProjectData','project_details',{'project_id':project_id})
    if proj['mltype'] == 'customersegmentation':
        return redirect(url_for('cust_report',project_id=project_id))
    
    
    proj_exception_logs = mongo.findRecordOnQuery('ProjectData','project_exceptions',{'project_id':project_id})
    proj_logs = mongo.findRecordOnQuery('ProjectData','project_logs',{'project_id':project_id})
    info = {
        'Project name':proj['project_title'],
        'Number Of Success Logs':len([i for i in proj_logs]),
        'Number Of Exception Logs':len([i for i in proj_exception_logs]),
        'train_status':proj['train_tag'],
        'predict_status':proj['predict_tag'],

    }
    if proj.get('train_successes',0) <1:
        logging.info(f"Didnot trained yet")
        flash("Model training hasn't been performed yet")
        return render_template('project_report.html',proj=proj,info=info)
    metrics = pd.DataFrame(proj['metrics'],columns=['standalone','boost','bag']).to_html()
    return render_template('project_report.html',info=info,proj=proj,metrics=metrics)

@app.route("/project_board/project_view/<project_id>/cust_proj_report", methods=['POST','GET'])
def cust_report(project_id):
    user_id = session['user_id']
    mongo = MongoDBmanagement(user_id,project_id)
        
    project=mongo.findfirstRecord('ProjectData','projects',{'project_id':project_id})
    proj = mongo.findfirstRecord('ProjectData','project_details',{'project_id':project_id})

    proj_exception_logs = mongo.findRecordOnQuery('ProjectData','project_exceptions',{'project_id':project_id})
    proj_logs = mongo.findRecordOnQuery('ProjectData','project_logs',{'project_id':project_id})
    info = {
        'Project name':proj['project_title'],
        'Number Of Success Logs':len([i for i in proj_logs]),
        'Number Of Exception Logs':len([i for i in proj_exception_logs]),
        'train_status':proj['train_tag'],

    }
    if proj.get('train_successes',0) <1:
        logging.info(f"Didnot trained yet")
        flash("Model training hasn't been performed yet")
        return render_template('cust_report.html',proj=project,info=info)
    
    if os.getenv('cloud_env')=='True':
        print('-------------------------------------cloud')
        predict_root = os.path.join(root_dir,'TrainingProcess')
        predict_folder = os.path.join(predict_root,'train_data',user_id,project_id)
        if not os.path.isdir(predict_folder):
            os.makedirs(predict_folder,exist_ok=True)
        
        cloud = project.get("cloud")
        user = mongo.findfirstRecord('UsersData','registered_users',{'user_id':user_id})
        user_name = user.get('user_name')
        predict_folder = os.path.join(root_dir,'PredictionProcess','predict_data',user_id,project_id)  
        if cloud == 'GCP':
            ops = GCPOps(user_id=user_id,project_id=project_id,user_name=user_name)
        elif cloud =='AWS':
            ops = AWSOps(user_id=user_id,project_id=project_id,user_name=user_name)
        print("--------------cloud",cloud)
        ops.get_directory(project_name=proj.get('project_title'),directory_path="prediction-files", download_path=predict_folder)
        file = os.path.join(predict_folder,f"{proj.get('project_title')}.csv")
    else:
        filename = f'{proj["project_title"]}-train.csv'
        predict_root = os.path.join(root_dir,'ValidationProcess',"TRAIN",'FINALDATA')
        predict_folder = os.path.join(predict_root,user_id,project_id,filename)
        file = predict_folder

    if file.endswith('.h5'):
        test_data = pd.read_hdf(file)
    else:
        test_data = pd.read_csv(file)

    graphs =SegmentAnalysis(test_data)
    seg_square = graphs.plot_cust_segment()
    seg_bar = graphs.plot_cust_bar()
    seg_line = graphs.plot_clv()
    desc_df = graphs.description()
    return render_template('cust_report.html',proj=project,
    desc_df = desc_df.to_html(index=True),
    seg_bar=seg_bar,
    seg_square=seg_square,
    seg_line=seg_line,
    info = info
    )

@app.route("/project_board/project_view/<string:project_id>/details", methods=['GET','POST'])
@cross_origin()
def project_details(project_id):
    user_id = session['user_id']
    mongo = MongoDBmanagement(user_id,project_id)
    proj = mongo.findfirstRecord('ProjectData','projects',{'project_id':project_id})
    print("--------proj0",proj)
    return render_template("details.html",proj=proj)

@cross_origin()
@app.route("/project_board/project_view/<string:project_id>/details_logs", methods=['GET','POST'])
def project_log_details_report(project_id):
    user_id = session['user_id']
    mongo = MongoDBmanagement(user_id,project_id)
    proj_details = mongo.findRecordOnQuery('ProjectData','project_details',{'project_id':project_id})
    if proj_details:
        return render_template('project_log_details_report.html',details = proj_details)
    else:
        return render_template('project_log_details_report.html',details = [])

def train_model_controller(user,project):
    logging.info("Started Train Model")
    user_name = user.get('user_name')
    user_id = user.get('user_id')
    project_id = project.get('project_id')

    mltype = project.get('mltype')
    project_title=project.get('project_title')

    preprocess_folder = os.path.join(root_dir,'TrainingProcess','preprocess_pipe',user_id,project_id) #made during validation
    batch_folder = os.path.join(root_dir,'TrainingProcess','batch_models',user_id,project_id) #made during validation
    train_folder = os.path.join(root_dir,'TrainingProcess','train_data',user_id,project_id)
    metrics_folder = os.path.join(root_dir,'TrainingProcess','metrics',user_id,project_id)
    if not os.path.isdir(train_folder): # extract from cloud
        os.makedirs(train_folder,exist_ok=True)
    if not os.path.isdir(batch_folder): # extract from cloud
        os.makedirs(batch_folder,exist_ok=True)
    if not os.path.isdir(preprocess_folder): # extract from cloud
        os.makedirs(preprocess_folder,exist_ok=True)
    if not os.path.isdir(metrics_folder): # extract from cloud
        os.makedirs(metrics_folder,exist_ok=True)

    try:
        if os.getenv('cloud_env')=='True':
            print('-------------------------------------cloud')
            warehouse = BigQueryManagement(project=project,user_id=user_id,type='train')
            file = warehouse.load_data(final_path=train_folder)
        else:
            filename=f"{project_title}-train.csv"
            file = os.path.join(root_dir,'ValidationProcess','TRAIN','FINALDATA',user_id,project_id,filename)
        # predict_root = os.path.join(root_dir,'ValidationProcess','TRAIN')
        # predict_folder = os.path.join(predict_root,'GOODRAWDATA',user_id,project_id,filename)
        # file = predict_folder
    
        mongo = MongoDBmanagement(user_id,project_id)
        logger = App_Logger(user_id,project_id)

        print('file',file)
        if file.endswith('.h5'):
            data = pd.read_hdf(file)
        else:
            data = pd.read_csv(file)
    except Exception as e:
        with app.app_context():
            logger.project_logs(f'Training Data couldnt be recieved from warehouse',exception=True,traceback = sys.exc_info())
           
            # send_mail(body=f'Project: {project_title} \n Training Data couldnt be recieved from warehouse',reciever = user.get('email'))
        print('--e',e)
        raise e
    with app.app_context():
            mongo.updateOneRecord('ProjectData','project_details',
            {'$set':{'train_tag':'progress','last_update':str(datetime.now())}},{'project_id':project_id})
        
            # send_mail(body='Model Training has been started, final files has been brought down from datawarehouse',reciever = user.get('email'))

       
    if mltype=='classification':
        cloud = project['cloud']
        train_schema = project.get('train_schema').replace("\'", "\"")
        dic = json.loads(train_schema)
        target = dic.get('Target')
        response = train_classif_model(data,target,user_id,user_name,project_id,project_title,cloud)

    elif mltype=='regression':
        cloud = project['cloud']
        train_schema = project.get('train_schema').replace("\'", "\"")
        dic = json.loads(train_schema)
        target = dic.get('Target')
        response = train_regress_model(data,target,user_id,user_name,project_id,project_title,cloud)

    elif mltype=='customersegmentation':
        cloud = project['cloud']
        schema = json.loads(project.get('train_schema').replace("\'", "\""))
        profit_margin = project.get('profit_margin',1)
        response = train_cust_project(data,schema,profit_margin,user_id,user_name,project_id,project_title,cloud)

    if os.getenv('cloud_env')=='True':
        if os.path.isfile(file):
            os.remove(file)

    if response['status'] == True:
        
        with app.app_context():
            logging.info(f"Metrics Here: {response['message']}")
            mongo.updateOneRecord('ProjectData','project_details',{'$set':{'train_tag':'completed','last_update':str(datetime.now()),'metrics':response['message']}},{'project_id':project_id})
            mongo.updateOneRecord('ProjectData','project_details',{'$inc':{'train_successes':1}},{'project_id':project_id})
            # send_mail(body=f'Project: {project_title} \nRegression Model Training has been completed succesfully',reciever = user.get('email'))
            pass
    
    else:
        with app.app_context():
            e = response['message']
            mongo.updateOneRecord('ProjectData','project_details',{'$set':{'train_tag':'failed','last_update':str(datetime.now())}},{'project_id':project_id})
            mongo.updateOneRecord('ProjectData','project_details',{'$inc':{'train_failures':1}},{'project_id':project_id})
            
            logger.project_logs(f'Model couldnt be trained on cloud {e}',exception=True,traceback = sys.exc_info())
            # send_mail(body=f'Project: {project_title} \n Model couldnt be trained on cloud, error: {e}',reciever = user.get('email'))
        print('--e',e)
    return {'status':'completed'}

def train_regress_model(data,target,user_id,user_name,project_id,project_title,cloud):
    preprocess_folder = os.path.join(root_dir,'TrainingProcess','preprocess_pipe',user_id,project_id) #made during validation
    batch_folder = os.path.join(root_dir,'TrainingProcess','batch_models',user_id,project_id) #made during validation
    metrics_folder = os.path.join(root_dir,'TrainingProcess','metrics',user_id,project_id)
    
    try:
        model = getregression.BestRegessionModel(data,target)
        model.fit()
        
        dump(model.preprocess_pipe,os.path.join(preprocess_folder,'preprocess_pipe.joblib'))
        metrics = model.scores_grid
        metrics['best_model_name'] = model.max_model.modelname
        dump(model,os.path.join(batch_folder,'batch-model.joblib'))
        dump(metrics,os.path.join(metrics_folder,'metrics.joblib'))

        if os.getenv('cloud_env')=='True':
            if cloud == 'GCP':
                ops = GCPOps(user_id=user_id,project_id=project_id,user_name=user_name)
            elif cloud =='AWS':
                ops = AWSOps(user_id=user_id,project_id=project_id,user_name=user_name)

            ops.upload_to_cloud(project_name=project_title,directory_path=preprocess_folder,dest_blob_folder='preprocess-pipe')
            ops.upload_to_cloud(project_name=project_title,directory_path=batch_folder,dest_blob_folder='train-batch-models')
            ops.upload_to_cloud(project_name=project_title,directory_path=metrics_folder,dest_blob_folder='metrics')
        
    except Exception as e:
        return {'status':False,'message':e}
    return {'status':True,'message':metrics}
    
def train_classif_model(data,target,user_id,user_name,project_id,project_title,cloud):
    preprocess_folder = os.path.join(root_dir,'TrainingProcess','preprocess_pipe',user_id,project_id) #made during validation
    batch_folder = os.path.join(root_dir,'TrainingProcess','batch_models',user_id,project_id) #made during validation
    metrics_folder = os.path.join(root_dir,'TrainingProcess','metrics',user_id,project_id)
    
    try:
        model = getclassification.BestClassificationModel(data,target)
        model.fit()
        
        dump(model.preprocess_pipe,os.path.join(preprocess_folder,'preprocess_pipe.joblib'))
        metrics = model.scores_grid
        dump(model,os.path.join(batch_folder,'batch-model.joblib'))
        dump(metrics,os.path.join(metrics_folder,'metrics.joblib'))

        if os.getenv('cloud_env')=='True':
            if cloud == 'GCP':
                ops = GCPOps(user_id=user_id,project_id=project_id,user_name=user_name)
            elif cloud =='AWS':
                ops = AWSOps(user_id=user_id,project_id=project_id,user_name=user_name)

            ops.upload_to_cloud(project_name=project_title,directory_path=preprocess_folder,dest_blob_folder='preprocess-pipe')
            ops.upload_to_cloud(project_name=project_title,directory_path=batch_folder,dest_blob_folder='train-batch-models')
            ops.upload_to_cloud(project_name=project_title,directory_path=metrics_folder,dest_blob_folder='metrics')
        
    except Exception as e:
        return {'status':False,'message':e}
    return {'status':True,'message':metrics}

def train_cust_project(data,schema,profit_margin,user_id,user_name,project_id,project_title,cloud):
    print('------------------------schema',schema['RFMCols'])
    schema = schema['RFMCols']
    id_col = schema.get('id_col',None)
    print(id_col)
    trans_col=schema.get('trans_col',None)
    print(trans_col)
    trans_date_col=schema.get('trans_date_col',None)
    print(trans_date_col)
    recency_col=schema.get('recency_col',None)
    frequency_col=schema.get('frequency_col',None)
    monetary_col=schema.get('monetary_col',None)
    age_col=schema.get('age_col',None)
    cal_rec=schema.get('cal_rec',None)
    cal_freq=schema.get('cal_freq',None)
    cal_mon=schema.get('cal_mon',None)
    predict_folder = os.path.join(root_dir,'PredictionProcess','predict_data',user_id,project_id)
    models_folder = os.path.join(root_dir,'TrainingProcess','batch_models',user_id,project_id)
    if not os.path.isdir(predict_folder):
        os.makedirs(predict_folder,exist_ok=True)
    if not os.path.isdir(predict_folder):
        os.makedirs(models_folder,exist_ok=True)

    segment = Segmentation(data=data)
    rfm_df = segment.calculate_ltv_df(id_col,trans_col,trans_date_col,recency_col,frequency_col,monetary_col,age_col,cal_rec,cal_freq,cal_mon,profit_margin)
    bgf,ggf = segment.bgf_model,segment.ggf_model
    print("models folder",models_folder)
    bgf.save_model(path = os.path.join(models_folder,'bgf_model.pkl'), save_data=False, save_generate_data_method=False)
    ggf.save_model(path=os.path.join(models_folder,'ggf_model.pkl'), save_data=False, save_generate_data_method=False)
    print(rfm_df.head())
    rfm_df.to_csv(os.path.join(predict_folder,f'{project_title}.csv'),index=False)
    
    if os.getenv('cloud_env')=='True':
        if cloud == 'GCP':
            ops = GCPOps(user_id=user_id,project_id=project_id,user_name=user_name)
        elif cloud =='AWS':
            ops = AWSOps(user_id=user_id,project_id=project_id,user_name=user_name)
        ops.upload_to_cloud(project_name=project_title,directory_path=predict_folder,dest_blob_folder='prediction-files')
        ops.upload_to_cloud(project_name=project_title,directory_path=models_folder,dest_blob_folder='batch-models')

    return {'status':True,'message':'Done'}


@app.route("/project_board/project_view/<string:project_id>/train", methods=['GET','POST'])
@login_required
def train_project(project_id):
    user_id = session['user_id']
    mongo = MongoDBmanagement(user_id,project_id)
    print('I am called for an action!')
    valid_tags = ['failed','validated','completed']
    project_tag = mongo.findfirstRecord('ProjectData','project_details',{'project_id':project_id}).get('train_tag')
    if project_tag not in valid_tags:
        logging.info("Cannot train model now, either files are not validated")
        flash("Cannot train model now, either files are not validated or model is already runnning")
        return redirect(url_for('dashboard'))

    project = mongo.findfirstRecord('ProjectData','projects',{'project_id':project_id})
    user = mongo.findfirstRecord('UsersData','registered_users',{'user_id':user_id})
    scheduler.add_job(train_model_controller,kwargs={'user':user,'project':project})
    return redirect(url_for('dashboard'))


def test_model(user,project):  
    user_name = user.get('user_name')
    user_id = user.get('user_id')
    project_id = project.get('project_id')
    cloud = project['cloud']
    mltype = project.get('mltype')
    project_title=project.get('project_title')
    batch_folder = os.path.join(root_dir,'PredictionProcess','batch_models',user_id,project_id)
    predict_folder = os.path.join(root_dir,'PredictionProcess','predict_data',user_id,project_id)
    if not os.path.isdir(predict_folder):
        os.makedirs(predict_folder,exist_ok=True)
    if not os.path.isdir(batch_folder):
        os.makedirs(batch_folder,exist_ok=True)

    if os.getenv('cloud_env')=='True':
        if cloud == 'GCP':
            ops = GCPOps(user_id=user_id,project_id=project_id,user_name=user_name)
        elif cloud =='AWS':
            ops = AWSOps(user_id=user_id,project_id=project_id,user_name=user_name)
    try:
        mongo = MongoDBmanagement(user_id,project_id)
        warehouse = BigQueryManagement(project=project,user_id=user_id,type='predict')
        logger = App_Logger(user_id,project_id)
        if os.getenv('cloud_env')=='True':
            file = warehouse.load_data(final_path=predict_folder)
            ops.get_directory(project_name=project_title,directory_path="train-batch-models", download_path=batch_folder)
        else:    
            file = predict_folder
        if file.endswith('.h5'):
            test_data = pd.read_hdf(file)
        else:
            test_data = pd.read_csv(file)
    except Exception as e:
        with app.app_context():
            logger.project_logs(f'final model cannot be loaded from cloud: {e}',exception=True,traceback = sys.exc_info())
            # send_mail(f'project:{project_title} \n final model cannot be loaded from cloud, error {e}',reciever=user.get('email'))
        print('--e',e)
        raise e
        return {'status':'failed'}
    try:
        with app.app_context():
            mongo.updateOneRecord('ProjectData','project_details',{'$set':{'predict_tag':'progress','last_update':str(datetime.now())}},{'project_id':project_id})
            # send_mail(body='Model Prediction has been started, final files drawn from datawarehouse',reciever = user.get('email'))
            logger.project_logs('project Prediction started!')
    
        if mltype=='classification':
            model = load(os.path.join(batch_folder,'batch-model.joblib'))
            predictions = model.predict(test_data)
            predict_df = pd.DataFrame(model.get_inverse_label(predictions),columns=['prediction'])
            predictions = model.get_inverse_label(predict_df)
            predict_df.to_csv(os.path.join(predict_folder,'final_predict.csv'),index=False)
        else:
            model = load(os.path.join(batch_folder,'batch-model.joblib'))
            predictions = model.predict(test_data)
            predict_df = pd.DataFrame(predictions,columns=['prediction'])
            predict_df.to_csv(os.path.join(predict_folder,'final_predict.csv'),index=False)
        if os.getenv('cloud_env')=='True':
            ops.upload_to_cloud(project_name=project_title,directory_path=predict_folder,dest_blob_folder='prediction-files')
        mongo.updateOneRecord('ProjectData','project_details',{'$set':{'predict_tag':'completed','last_update':str(datetime.now())}},{'project_id':project_id})
      
    except Exception as e:
        with app.app_context():
            mongo.updateOneRecord('ProjectData','project_details',{'$set':{'predict_tag':'failed','last_update':str(datetime.now())}},{'project_id':project_id})
            logging.info(f"{e}")
            logger.project_logs(f'Prediction couldnt be made on cloud {e}',exception=True,traceback = sys.exc_info())
            # send_mail(body=f'Project: {project_title} \n Prediction couldnt be made on cloud, error:{e}',reciever = user.get('email'))
        print('-e',e)
        raise e
        return {'status':'failed'}
             
    if os.getenv("cloud_env")=='True':
        if os.path.isfile(file):
            os.remove(file)
    with app.app_context():
        # send_mail(body=f'Project: {project_title} \nModel Prediction has been completed succesfully, navigate to file management to retrieve file',reciever = user.get('email'))
        pass
    return {'status':'completed'}

@app.route("/project_board/project_view/<project_id>/test", methods=['POST','GET'])
def test_project(project_id):
    user_id = session['user_id']
    mongo = MongoDBmanagement(user_id=user_id,project_id=project_id)
    logger = App_Logger(user_id,project_id)
    print('I am called for an action! testing')
    valid_tags = ['failed','validated','completed']
    project_detail = mongo.findfirstRecord('ProjectData','project_details',{'project_id':project_id})
    predict_tag = project_detail.get('predict_tag')
    train_tag = project_detail.get('train_tag')

    if train_tag not in valid_tags:
        logging.info(f"Cannot make prediction now, either files are not added or a model is already runnning")
        flash("Cannot make prediction now, either files are not added or a model is already runnning")
        return redirect(url_for('project_board'))
    if predict_tag not in valid_tags:
        logging.info(f"Cannot make prediction now, either files are not added or a model is already runnning")
        flash("Cannot make prediction now, either files are not added or a model is already runnning")
        return redirect(url_for('project_board'))

    project = mongo.findfirstRecord('ProjectData','projects',{'project_id':project_id})
    user = mongo.findfirstRecord('UsersData','registered_users',{'user_id':user_id})
    scheduler.add_job(test_model,kwargs={'user':user,'project':project})
    return {'status':'initiated'}


@app.route("/add_cust_files/<project_id>",methods=['POST','GET'])
def add_cust_files(project_id):
    user_id = session['user_id']
    print('called!')
    if request.method=='POST':
        print('yes')
        train_root = os.path.join(root_dir,'ValidationProcess','TRAIN')
        train_folder = os.path.join(train_root,'RAWDATA',user_id,project_id)
        if not os.path.isdir(train_folder):
            os.makedirs(train_folder,exist_ok=True)
        train_files = request.files.getlist('trainfile[]')
        files = [secure_filename(file.filename) for file in train_files if file.filename!='']
        if files:
            print('================6++6====-=-=',files)
            for file_num in range(len(train_files)):
                filename = os.path.join(train_folder,files[file_num])
                train_files[file_num].save(filename)
                print("saved")
            job = scheduler.add_job(validate_insert_train,
        kwargs={'user_id':user_id,'project_id':project_id,'folder_path':train_folder,
        'type':'train','user_root':train_root})
        predict_root = os.path.join(root_dir,'ValidationProcess','PREDICT')
        predict_folder = os.path.join(predict_root,'RAWDATA',user_id,project_id)
        if not os.path.isdir(predict_folder):
            os.makedirs(predict_folder,exist_ok=True)
        predict_files = request.files.getlist('predictfile[]')
        files = [secure_filename(file.filename) for file in predict_files if file.filename!='']
        if files:
            print('====================-=-=',files)
            for file_num in range(len(predict_files)):
                filename = os.path.join(predict_folder,files[file_num])
                predict_files[file_num].save(filename)
                print("saved")
            job = scheduler.add_job(validate_insert_predict,
            kwargs={'user_id':user_id,'project_id':project_id,'folder_path':predict_folder,
            'type':'predict','user_root':predict_root})
        
        flash("files have been recieved, they wll be uploaded to cloud after validation!")
        return redirect(url_for('project_board'))
    return redirect(url_for('config_project'))


# port = int(os.getenv("PORT",5001))
if __name__ == "__main__":
    port = 8080
    host = '0.0.0.0'
    # app.run(host=host,port=port,debug=True,threaded=True)
    # app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
    app.run(debug=True,threaded=True)
    # app.config['FLASK_ENV'] = 'development'
    # app.config['DEBUG'] = True
    # host = 
    # port = int(os.environ.get('PORT',8080))
    # httpd = simple_server.make_server(host, port, app)
    # print("Serving on %s %d" % (host, port))
    # httpd.serve_forever()

    # app.config['TESTING'] = True