import numpy as np

class BaseRegressor():
    """For Ensuring format of regression model
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
        self.is_gpu_enabled = is_gpu_enabled
        self.tune_grid = tune_grid
        self.tune_args = tune_args
        self.preprocess_steps={}

        self.is_boosting_supported = True
        self.is_soft_voting_supported = True
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

class BaseLinearRegressor(BaseRegressor):

    def __init__(self) -> None:
        from sklearn.linear_model import LinearRegression
        args = {}
        tune_args = {}
        tune_grid = {"fit_intercept": [True, False]}
        preprocess_steps = {'scale_data':True,'dummify_categoricals':True}

        super().__init__(
            id="lr",
            name="Linear Regression",
            class_def=LinearRegression(),
            args=args,
            tune_grid=tune_grid,
            tune_args=tune_args,
            preprocess_steps = preprocess_steps,
        )

class BaseLassoRegressor(BaseRegressor):

    def __init__(self) -> None:
        from sklearn.linear_model import Lasso
        args = {}
        tune_args = {}
        tune_grid = {
            "alpha": np.arange(0.1, 5, 0.5),
            "fit_intercept": [True, False],
        }
        preprocess_steps = {'scale_data':True,'dummify_categoricals':True}

        super().__init__(
            id="lasso",
            name="Lasso Regression",
            class_def=Lasso(),
            args=args,
            tune_grid=tune_grid,
            tune_args=tune_args,
            preprocess_steps = preprocess_steps,
        )

class BaseElasticNetRegressor(BaseRegressor):

    def __init__(self) -> None:
        from sklearn.linear_model import ElasticNet
        args = {}
        tune_args = {}
        tune_grid = {
            "alpha": np.arange(0.1, 5, 0.55),
            "l1_ratio": np.arange(0.1, 1, 0.5),
            "fit_intercept": [True, False],
        }
        preprocess_steps = {'scale_data':True,'dummify_categoricals':True}
        super().__init__(
            id="elnet",
            name="Elastic Regression",
            class_def=ElasticNet(),
            args=args,
            tune_grid=tune_grid,
            tune_args=tune_args,
            preprocess_steps = preprocess_steps,
        )

class BaseSVRRegressor(BaseRegressor):
    def __init__(self, ) -> None:
        
        from sklearn.svm import SVR
        args = {}
        tune_args = {}
        tune_grid = {
            "C": np.arange(0.1, 1.5, 0.4),
            "epsilon": [1.1, 1.8, 1.9], #1.35, 1.4, 1.5, 1.55, 1.6,1.3,  1.7, 1.2,
            'kernel' : ['linear', 'rbf', ],
        }
        preprocess_steps = {'scale_data':True,'dummify_categoricals':True}
        super().__init__(
            id="svr",
            name="Support Vector Regression",
            class_def=SVR(),
            args=args,
            tune_grid=tune_grid,
            tune_args=tune_args,
            preprocess_steps = preprocess_steps,
        )

class BaseKNeighborsRegressor(BaseRegressor):
    def __init__(self, ) -> None:
    
        from sklearn.neighbors import KNeighborsRegressor
        args = {}
        tune_args = {}
        tune_grid = {"n_neighbors":np.arange(2,10),
                     "weights":["uniform"]}
        preprocess_steps = {'scale_data':True,'dummify_categoricals':True}


        super().__init__(
            id="knn",
            name="K Neighbors Regressor",
            class_def=KNeighborsRegressor(),
            args=args,
            tune_grid=tune_grid,
            tune_args=tune_args,
            preprocess_steps = preprocess_steps,
        )

class BaseDecisionRegressor(BaseRegressor):
    def __init__(self,) -> None:
        from sklearn.tree import DecisionTreeRegressor

        args = {}
        tune_args = {}
        tune_grid = {
            "max_depth": np.arange(4, 10, 1),
            "max_features": ["auto"], # 1.0, 
            "min_samples_leaf": [2,  6], #3, 4, 5,
            "min_samples_split": [2, 10], #5, 7, 9,
            "min_impurity_decrease": [
                0,
                # 0.0001,
                # 0.001,
                # 0.01,
                # 0.0002,
                # 0.002,
                # 0.02,
                # 0.0005,
                # 0.005,
                # 0.05,
                # 0.1,
                0.2,
                # 0.3,
                # 0.4,
                0.5,
            ],
            "criterion": ["mse"], # , "mae", "friedman_mse"
        }
        preprocess_steps={'scale_data':False,'dummify_categoricals':True}

        super().__init__(
            id="dt",
            name="Decision Tree Regressor",
            class_def=DecisionTreeRegressor(),
            args=args,
            tune_grid=tune_grid,
            
            tune_args=tune_args,
            preprocess_steps = preprocess_steps,
        )

class BaseRandomForRegressor(BaseRegressor):
    def __init__(self, ) -> None:
        

        from sklearn.ensemble import RandomForestRegressor
      
        tune_args = {}
        tune_grid = {
            "n_estimators": np.arange(10, 100, 10),
            "max_depth": np.arange(4, 11, 1),
            "min_impurity_decrease": [
                0.0002,
                0.002,
            ],
            "max_features": [ "auto"], # 1.0,
            "bootstrap": [True, False],
        }
        preprocess_steps={'scale_data':False,'dummify_categoricals':True}
        super().__init__(
            id="rf",
            name="Random Forest Regressor",
            class_def=RandomForestRegressor(),
            tune_grid=tune_grid,
            tune_args=tune_args,
            preprocess_steps=preprocess_steps,
        )