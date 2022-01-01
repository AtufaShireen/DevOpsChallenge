import numpy as np


class BaseClassifier():
    """For Ensuring format of classification  model
    id: for index,
    name: display name,
    class_def: model name,
    tune_grid: hyperparameters to tune,
    is_gpu_enabled: default: None
    preprocess_steps(in future): preprocess steps as per model
    """
    def __init__(
        self,id,name,class_def,tune_grid,args={},
        tune_args={},
        is_gpu_enabled=False,preprocess_steps={},random_state=45):
        
        if not args:
            args = {}
        if not tune_grid:
            tune_grid = {}
        if not tune_args:
            tune_args = {}
        if not preprocess_steps:
            preprocess_steps= {}
        self.args = args
        self.tune_grid = tune_grid
        self.tune_args = tune_args
        self.preprocess_steps=preprocess_steps
        self.id= id
        self.name = name
        self.class_def = class_def


    def get_dict(self):
        """
        TO get model properties
        """
        d = [
            ("ID", self.id),
            ("Name", self.name),
                ("Class", self.class_def),
                ("Args", self.args),
                ("Tune Grid", self.tune_grid),
                ("Tune Args", self.tune_args),
        ]

        return dict(d)

#noq
class BaseLogisticRegression(BaseClassifier):
    def __init__(self, ) :
        
        from sklearn.linear_model import LogisticRegression

        
        args = {}
        tune_args = {}
        tune_grid = {"C":np.arange(0.5, 3, 0.2),"max_iter": [1000],"solver":["saga","lbfgs"]}
        
        
        preprocess_steps = {'scale_data':True,'dummify_categoricals':True,'fit_le':True}
        super().__init__(
            id="lr",
            name="Logistic Regression",
            class_def=LogisticRegression(),
            args=args,
            tune_grid=tune_grid,
            tune_args=tune_args,
            preprocess_steps=preprocess_steps,
        )

#noq
class BaseKNeighborsClassifier(BaseClassifier):
    def __init__(self, ) :
        from sklearn.neighbors import KNeighborsClassifier
        args = {}
        tune_args = {}
        tune_grid = {"n_neighbors":np.arange(1, 5),"weights":["uniform"],"metric":["euclidean"]}
        
        preprocess_steps = {'scale_data':False,'dummify_categoricals':False}
        super().__init__(
            id="knn",
            name="K Neighbors Classifier",
            class_def=KNeighborsClassifier(),
            args=args,
            tune_grid=tune_grid,
            tune_args=tune_args,
            preprocess_steps=preprocess_steps,
        )


class BaseGaussianNB(BaseClassifier):
    def __init__(self, ) :
        preprocess_steps = {'scale_data':False,'dummify_categoricals':False}
        from sklearn.naive_bayes import GaussianNB
        args = {}
        tune_args = {}
        tune_grid = {
            "var_smoothing": [
                0.003,
                0.004,
            ]
        }
        
        super().__init__(
            id="nb",
            name="Naive Bayes",
            class_def=GaussianNB(),
            args=args,
            tune_grid=tune_grid,
            tune_args=tune_args,
            preprocess_steps=preprocess_steps,
        )

#noq
class BaseDecisionTreeClassifier(BaseClassifier):
    def __init__(self, ):
        preprocess_steps = {'scale_data':False,'dummify_categoricals':False}
        from sklearn.tree import DecisionTreeClassifier

        args = {}
        tune_args = {}
        tune_grid = {
            "max_depth": np.arange(4, 10, 1),
            "max_features": ["auto"],
            "min_samples_leaf": [2, 3], #, 4, 5, 6
            "min_samples_split": [2, 5], #, 7, 9, 10
            "criterion": ["gini", "entropy"],
            "min_impurity_decrease": [
                0,
                0.0001,
                0.3,
                0.4,
                0.5,
            ],
        }        

        super().__init__(
            id="dt",
            name="Decision Tree Classifier",
            class_def=DecisionTreeClassifier(),
            args=args,
            tune_grid=tune_grid,
            tune_args=tune_args,
            preprocess_steps=preprocess_steps
        )

#noq
class BaseSGDClassifier(BaseClassifier):
    def __init__(self, ) :
        preprocess_steps = {'scale_data':True,'dummify_categoricals':False}
        from sklearn.linear_model import SGDClassifier


        args = {}
        tune_args = {}
        tune_grid = {
            "penalty": [ "l2", "l1"],
            "l1_ratio": np.arange(0.1, 1, 0.5),#000000.1
            "alpha": [
                0.0000001,
                # 0.001,
                # 0.005,
                # 0.4,
                0.5,
            ],
            "fit_intercept": [True, False],
            "learning_rate": ["constant", "invscaling"], #, "adaptive", "optimal"
            "eta0": [0.001, 0.5], #, 0.05, 0.1,
            "early_stopping":[True], #0.2, 0.3, 0.4
        }
        super().__init__(
            id="sgd",
            name="SVM - Linear Kernel",
            class_def=SGDClassifier(),
            args=args,
            tune_grid=tune_grid,
            tune_args=tune_args,
            preprocess_steps=preprocess_steps,
        )


class BaseSVC(BaseClassifier):
    def __init__(self, ) :
        preprocess_steps = {'scale_data':True,'dummify_categoricals':False}
        from sklearn.svm import SVC   
        args = {
            
        }
        tune_args = {}
        tune_grid = {
            "gamma": ["auto"],
            "probability": [True],
            "kernel": ["rbf"],
            "random_state": [45],
            "C": np.arange(0.5, 5, 0.8), #>0
            "class_weight": ["balanced"],
        }
        super().__init__(
            id="svc",
            name="SVM - Radial Kernel",
            class_def=SVC(),
            args=args,
            tune_grid=tune_grid,
            
            tune_args=tune_args,
            preprocess_steps=preprocess_steps,
        )


class BaseRandomForestClassifier(BaseClassifier):
    def __init__(self, ) :
        preprocess_steps = {'scale_data':False,'dummify_categoricals':False}
        from sklearn.ensemble import RandomForestClassifier

        tune_args = {}
        tune_grid = {
            "n_estimators": np.arange(10, 300, 10),
            "max_depth": np.arange(5, 11, 1),
            "min_impurity_decrease": [
                0.0001,
                0.1,
                0.5,
            ],
            "max_features": ["auto"],
            "bootstrap": [True, False],
            "criterion":["gini", "entropy"],
            "class_weight":["balanced",],
            "min_samples_split":[2,  10], #5, 7, 9
            "min_samples_leaf": [2, 6] # 3, 4,5, 
        }

        

        super().__init__(
            id="rf",
            name="Random Forest Classifier",
            class_def=RandomForestClassifier(),
            tune_grid=tune_grid,
            
            tune_args=tune_args,
        )
