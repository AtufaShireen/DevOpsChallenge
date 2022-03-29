
from sklearn.base import BaseEstimator
from automl.models.utils import *
from sklearn.base import clone
# import matplotlib.pyplot as plt
import scikitplot as skplt

class ClassifyModel(BaseEstimator):
    '''
    Create and returns model for classification with best parameters
    using bayesian optimisation.
    Pass id as estimator (refer utils.py, classify_model) to create standalone model
    eg:
    >>> model = Classify_model(X,y,estimator='dt')
    >>> model.fit()    
    >>> model.predict(X)
    '''
    def __init__(self,X,y,estimator):
        self.modelbase = classify_models[estimator]
        self.modelname=self.modelbase.name
        self.x_train,self.y_train = X,y
        self.model = clone(self.modelbase.class_def)

    def fit(self,X=None,y=None):
        if (X==None) and (y==None):
            X = self.x_train
            y = self.y_train
        tune_grid = self.modelbase.tune_grid
        
        self.best_param,self.best_cv_score = get_best_param(estimator=self.model,X = X,y = y,tune_grid=tune_grid,)
        self.model.set_params(**self.best_param)
        self.model.fit(X,y)
        
    def get_params(self,deep=True): 
        return (self.best_param)
    
    def best_score(self):
        return self.best_cv_score
        
    def predict(self,X,y=None):
        predictions = self.model.predict(X)
        return predictions
    
    def predict_proba(self,X,y=None):
        predictions = self.model.predict_proba(X)
        return predictions
    
    def score(self,X,y):
        return self.model.score(X,y)
    
    def plot_model(self):
        probas = self.model.predict_proba(self.x_test)
        # Now plot.

        skplt.metrics.plot_precision_recall( self.y_test,probas)
        img = plot_config(title=self.modelname,xlabel='FPR',ylabel='TPR')
        return img
