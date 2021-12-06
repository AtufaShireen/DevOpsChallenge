from logging import log
from automl.models.utils import *
from automl.models.mlalgos import regression,ensemble
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error,mean_squared_error,r2_score
from automl.preprocessing.preprocessor import preprocess_path
import inspect

logging.basicConfig(level=logging.INFO)
class BestRegessionModel():
    '''
    0) perform preprocessing
        Default:
        1) Remove duplicate rows
        2) Remove duplicate columns
        3) Remove columns with zero standard deviation
        4) Remove datetime columns
        5) perform standard scaler
        6) dummifiy categoricals

    1) split data into train_ and test_ data

    2) get best standalone regression model out of n (train_)
        Repeat for every regression model (specified in utils.py)
        1) split data in random k-folds(10)
        2) perform hyper parameter tuning with bayesian optimisation
        3) select the model with best cv score

    3) get best boosting model out of n (train_)
        Repeat for every boosting model (specified in utils.py)
        1) split data in random k-folds(10)
        2) perform hyper parameter tuning with bayesian optimisation
        3) select the model with best cv score
    
    4) get best bagging model out of n (train_)
        Repeat for every bagging model (specified in utils.py)
        1) select all base models (specified in utils.py)
        2) select tune grid of all models and add to bagging model's tune grid
        3) perform hyper parameter tuning with bayesian optimisation
              (basically same as optimizing base model parameters)
        4) select the model with best cv score
    
    5) select best model (from standalone,bag,boost) with rmse score (test_)

    6) Again perform fit to meta data with parameter tuning

    Eg:
    >>>    data_train = pd.read_csv('file')
    >>>    target = 'variety'
    >>>    model = BestRegessionModel(data = data_train,target=target)
    >>>    model.fit()
    
    >>>    data_test = pd.read_csv('file')
    >>>    predictions = model.predict(data_test)   
    >>>    print(f1score(test_y,predictions))   
    '''
    def __init__(self,data,target,preprocess=True,preprocess_steps={},*args,**kwargs):
        self.data = data
        self.target = target
        self.scores_grid = {}
        self.preprocess = preprocess
        if preprocess:
            if preprocess_steps:
                steps = inspect.getargspec(preprocess_path).args
                for key in preprocess_steps.keys():
                    if key not in steps:
                        raise ValueError("Invalid Parameter")
                try:
                    self.preprocess_pipe = preprocess_path(data=self.data,ml_type='regression',target=target,**preprocess_steps)
                    print("Done")
                    print(self.preprocess_pipe)
                except Exception as e:
                    logging.info(f"Invalid value passed {e}")
                    raise ValueError("Invalid value passed to parameter")
            else:
                self.preprocess_pipe = preprocess_path(data=self.data,ml_type='regression',scale_data=True,scaling_method="zscore",
                    target=self.target,dummify_categoricals=True,cluster_entire_data=False)
            
    def fit(self):
        logging.info(f'Started ,FGetting Best model')
        if self.preprocess:
            logging.info(f"Preprocessing the Training data")  
            self.data = self.preprocess_pipe.fit_transform(self.data)
        X=self.data.drop(self.target,axis=1)
        if 'cluster_label' in X.columns:
            X.drop('cluster_label',axis=1,inplace=True)
        y = self.data[self.target]
        self.meta_x_train,self.meta_x_test,self.meta_y_train,self.meta_y_test = train_test_split(X,y,test_size=0.33)
        self.standalone_model_ = self.get_best_standalone_estimate(self.meta_x_train,self.meta_y_train)
        self.boost_model_ = self.get_best_boost(self.meta_x_train,self.meta_y_train)
        self.bag_model_ = self.get_best_bag(self.meta_x_train,self.meta_y_train)
        standalone_ = self.standalone_model_.predict(self.meta_x_test)
        boost_ = self.boost_model_.predict(self.meta_x_test)
        bag_ = self.bag_model_.predict(self.meta_x_test)

        self.scores_grid = {
            'standalone': {
                'r2': r2_score(self.meta_y_test,standalone_),
                'mae':mean_absolute_error(self.meta_y_test,standalone_),
                'mse': mean_squared_error(self.meta_y_test,standalone_),
                'rmse': mean_squared_error(self.meta_y_test,standalone_,squared=False),
            },
            'boost': {
                'r2': r2_score(self.meta_y_test,boost_),
                'mae':mean_absolute_error(self.meta_y_test,boost_),
                'mse': mean_squared_error(self.meta_y_test,boost_),
                'rmse': mean_squared_error(self.meta_y_test,boost_,squared=False),
            },
            'bag': {
                'r2': r2_score(self.meta_y_test,bag_),
                'mae':mean_absolute_error(self.meta_y_test,bag_),
                'mse': mean_squared_error(self.meta_y_test,bag_),
                'rmse': mean_squared_error(self.meta_y_test,bag_,squared=False),
            },

        }
        logging.info(f'Model Scores:{self.scores_grid}')
        max_score = float('-inf')
        for model,method in self.scores_grid.items():
            if method['rmse'] >= max_score:
                max_score = method['rmse']
                if model == 'standalone':
                    max_model =self.standalone_model_
                elif model == 'boost':
                    max_model =self.boost_model_
                elif model == 'bag':
                    max_model = self.bag_model_
        logging.info(f'Best model was,:{max_model}')
        self.max_model = max_model
        self.max_model.model.fit(X,y)

    def get_best_standalone_estimate(self,x_train,y_train):
        logging.info(f'Looking for best standalone model')
        # regress_best_model = {} for storing complete info of best model
        self.all_regress_model_score = {}
        score_ =float('-inf')
        estimates = ['lr', 'dt','lasso','svr','knn','elnet','rf']

        for i in estimates:
            # model.drop(['cluster_label'],axis=1,inplace=True)
            model = regression.RegressModel(X=x_train,y=y_train,estimator=i)
            logging.info(f'Fitting standalone model: {i}')
            model.fit()
            logging.info(f'standalone model complete: {i}')
            self.all_regress_model_score[i] = {
                'modelname':model.modelname,
                'modelscore':model.best_score(),
                'modelparams':model.get_params(),
            }
            if model.best_score() > score_:
                score_ = model.best_cv_score # update score
                best_model = model
        logging.info("Best model Found, {best_model")
        return best_model

    def get_best_boost(self,x_train,y_train):
        logging.info(f'Looking for best boosting model')
        self.all_boost_model_score={}
        estimates = ['xgboost']
        score_ =float('-inf')
        for i in estimates:
            logging.info(f'Fitting Boosting model: {i}')
            model = ensemble.BoostingEnsemble(X=x_train,y=y_train,estimator=i,ml_type='regression')
            model.fit()
            logging.info(f'Fitting Complete: {i}')
            self.all_boost_model_score[i] = {
                'modelname':model.modelname,
                'modelscore':model.best_score(),
                'modelparams':model.get_params(),
            }

            if model.best_score() > score_:
                score_ = model.best_cv_score # update score
                best_model = model
        logging.info(f'Best model finding Complete:{best_model}')
        return best_model

    def get_best_bag(self,x_train,y_train):
        logging.info(f'Looking for best bagging model')
        all_bag_model_score={}
        estimates = ['vc']
        score_ =float('-inf')
        for i in estimates:
            logging.info(f'Fitting Bagging model: {i}')
            model = ensemble.RegressBaggingEnsemble(X=x_train,y=y_train,estimator=i)
            model.create_bagging_model()
            logging.info(f'Bagg created model: {i}')
            model.fit()
            logging.info(f'Fitting Bag  model: {i}')
            all_bag_model_score[i] = {
                'modelname':model.modelname,
                'modelscore':model.best_score(),
                'modelparams':model.get_params(),
            }
            
            if model.best_score() > score_:
                score_ = model.best_cv_score # update score
                best_model = model
        logging.info(f'Found model: {best_model}')
        return best_model

    def predict(self,X):
        X =self.preprocess_pipe.transform(X)
        if 'cluster_label' in X.columns:
            X.drop('cluster_label',axis=1,inplace=True)
        return self.max_model.model.predict(X)

    
    # def preprocess_data(self,**kwargs):
    #     logging.info(f'Started Preprocessing to train data')
    #     self.preprocess_pipe = preprocess_path(data=self.data,ml_type='regression',scale_data=True,scaling_method="zscore",
    #                     target=self.target,dummify_categoricals=True,cluster_entire_data=False,**kwargs)
    #     self.preprocess_pipe.fit_transform(self.data)

    # def inverse_preprocess_data(self,data):
    #     logging.info(f'Started Preprocessing for prediction data')
    #     self.preprocess_pipe.transform(data)
    #     return data

    # def get_preprocess_pipe(self):
    #     return self.preprocess_pipe