
from sklearn.base import BaseEstimator
from automl.models.utils import *
from sklearn.base import clone
import logging
from sklearn.model_selection import StratifiedKFold
import pandas as pd
logging.basicConfig(level=logging.INFO)

class ClassifBaggingEnsemble(BaseEstimator):
    ''' Supported: Voting Classifier,
        default: Voting Classifier
        eg:
        >>> modelbase = BaggingEnsemble(X,y)
        >>> modelbase.create_bagging_model() #adds base models to bag
        >>> modelbase.fit()
        >>> model.predict(X)

    '''
   
    def __init__(self,X,y,estimator):
        self.estimator = estimator
        self.x_train,self.y_train = X,y
        self.modelbase = classif_bag_model[estimator]
        self.model = clone(self.modelbase.class_def)
        self.modelname = self.modelbase.name

    def base_model_grids(self,id):
        # changing grid of every base estimator as per required by esemble model for hyper parameter tuning
        modelbase = classify_models[id]
        modelname=modelbase.name
        model_class = modelbase.class_def
        tune_grid = modelbase.tune_grid
        
        tune_grid = {f'{id}__{k}':v for k,v in tune_grid.items()}
        
        return tune_grid
    
    def base_model(self,id):
        '''Creating base models of Bag'''
        modelbase = classify_models[id]
        modelname=modelbase.name
        model_class = modelbase.class_def
        model = clone(model_class)
        return model
    
    def fit(self,X=None,y=None):
        if (X==None) and (y==None):
            X = self.x_train
            y = self.y_train        
        self.model.set_params(estimators=self.base_ensemble_models())
        tune_grid = self.modelbase.tune_grid
        self.best_params,self.best_cv_score = get_best_param(estimator=self.model,X =X,y = y,tune_grid=tune_grid)
        self.model.set_params(**self.best_params)
        self.model.fit(self.x_train,self.y_train)
        # return model
    
    def get_params(self):
        return self.best_params

    def best_score(self):
        return self.best_cv_score
    
    def create_bagging_model(self):
        '''supported: voting classifier,
           ensemble_id:'vc' for voting classifier,
            base_models: rf,dt,lr (classification)
           '''
        tune_grid = {}
        estimators  = self.base_ensemble_models()
        for i in estimators:
            for k,v in self.base_model_grids(i[0]).items():
                tune_grid[k] = v
        self.modelbase.tune_grid = tune_grid

    def predict(self,X,y=None):
        return self.model.predict(X)
    
    def base_ensemble_models(self):
        # Instantiate classifiers
        dt = self.base_model(id = 'dt')
        nb = self.base_model(id='nb')
        estimators = [('dt',dt),('nb',nb)]
        return estimators
 
    def score(self,X,y):
        return self.model.score(X,y)

class RegressBaggingEnsemble(BaseEstimator):
    ''' Supported: Voting Regressor,
        default: Voting Regressor
        eg:
        >>> modelbase = BaggingEnsemble(X,y)
        >>> modelbase.create_bagging_model() #adds base models to bag
        >>> modelbase.fit()
        >>> model.predict(X)

    '''
   
    def __init__(self,X,y,estimator):
        self.estimator = estimator
        self.x_train,self.y_train = X,y
        self.modelbase = regress_bag_model[estimator]
        self.model = clone(self.modelbase.class_def)
        self.modelname = self.modelbase.name
    
    def base_model_grids(self,id):
        # changing grid of every base estimator as per required by esemble model for hyper parameter tuning
        modelbase = regress_models[id]
        modelname=modelbase.name
        model_class = modelbase.class_def
        tune_grid = modelbase.tune_grid
        
        tune_grid = {f'{id}__{k}':v for k,v in tune_grid.items()}
        
        return tune_grid

    def base_model(self,id):
        '''Creating base models of Bag'''
        modelbase = regress_models[id]
        modelname=modelbase.name
        model_class = modelbase.class_def
        model = clone(model_class)
        return model
    
    def fit(self,X=None,y=None):
        if (X==None) and (y==None):
            X = self.x_train
            y = self.y_train        
        self.model.set_params(estimators=self.base_ensemble_models())
        tune_grid = self.modelbase.tune_grid
        self.best_params,self.best_cv_score = get_best_param(estimator=self.model,X = self.x_train,y = self.y_train,tune_grid=tune_grid)
        self.model.set_params(**self.best_params)
        self.model.fit(self.x_train,self.y_train)
        # return model

    def get_params(self):
        return self.best_params

    def best_score(self):
        return self.best_cv_score
        
    def create_bagging_model(self):
        '''supported: voting regressor,
           ensemble_id:'vc' for voting regressor,
            base_models: lr,svr (regression)
           '''
        tune_grid = {}
        estimators  = self.base_ensemble_models()
        for i in estimators:
            for k,v in self.base_model_grids(i[0]).items():
                tune_grid[k] = v
        self.modelbase.tune_grid = tune_grid

    def predict(self,X,y=None):
        return self.model.predict(X)

    def base_ensemble_models(self):
        # Instantiate Regressions
        lasso = self.base_model(id='lasso')
        dt = self.base_model(id='dt') 
        estimators = [('lasso',lasso),('dt',dt)]
        return estimators
    
    def score(self,X,y):
        return self.model.score(X,y)
 
#since not many changes in classification vs regression fitting technique they are combined        
class BoostingEnsemble(BaseEstimator):
    ''' Supported Xgboost
          eg:
        >>> modelbase = BoostingEnsemble(data=data,target=target,ml_type='regression')
        >>> model = modelbase.create_boosting_model()
        >>> model.fit()
        >>> modelbase.score() # accuracy of model based on 2% hold out train data set
        >>> model.predict(X)

    '''
    def __init__(self,X,y,ml_type,estimator='xgboost'):
        self.ml_type = ml_type
        self.x_train, self.y_train = X,y
        if self.ml_type=='regression':
            self.modelbase = regress_boost_model[estimator]
        else:
            self.modelbase = classif_boost_model[estimator]
        self.modelname = self.modelbase.name
        
        self.model = clone(self.modelbase.class_def)

    def fit(self,X=None,y=None):

        if (X is None):
            X = self.x_train   
        if (y is None):
            y = self.y_train
        if (self.ml_type=='classification'): #multiclass classification
            num_class = y.nunique()
            if (num_class >2):
                self.model.set_params(n_jobs=-1,    
                        use_label_encoder=False,
                        objective="multi:softmax",
                        eval_metric="merror",
                        verbosity=0,
                        num_class=len(set(y)))
        tune_grid=self.modelbase.tune_grid
        try:
            self.best_params,self.best_cv_score = get_best_param(estimator=self.model,X = X,y = y,tune_grid=tune_grid)
        except Exception as e:
            logging.info(f"Couldnot perform boosting {e}")
            raise ValueError("Pass Sufficient data")
        self.model.set_params(**self.best_params)
        self.model.fit(X,y)

    def get_params(self,deep=True):
        return (self.best_params)

    def best_score(self):
        return self.best_cv_score
    def predict(self,X,y=None):
        predictions = self.model.predict(X)
        return predictions
    
    def score(self,X,y):
        test_score = self.model.score(X,y)
        return test_score
