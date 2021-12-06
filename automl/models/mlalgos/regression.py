import numpy as np
from sklearn.base import BaseEstimator
from sklearn.base import clone
from automl.models.utils import *

class RegressModel(BaseEstimator):
    '''
    Create and returns model for regression with best parameters
    using bayesian optimisation.
    Pass estimator id (refer utils.py, regress_model) create standalone model
        eg:
    >>> modelbase = RegressModel(X,y,estimator='lr')
    >>> model.fit()
    >>> model.predict(X)
    >>> model.score(X,y)

    '''
    def __init__(self,X,y,estimator):

        self.modelbase = regress_models[estimator]
        self.modelname=self.modelbase.name
        self.x_train, self.y_train = X,y
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

    def score(self,X,y):
        return self.model.score(X,y)

    def plot_model(self):
        train_acc = self.score(self.x_train, self.y_train)
        test_acc = self.score(self.x_train, self.y_train)
        plt.bar(x=['train accuracy','test accuracy'],height=[train_acc,test_acc],width=0.4)
        img = plot_config(title='r2',xlabel='data',ylabel='accuracy')
        return img
        
