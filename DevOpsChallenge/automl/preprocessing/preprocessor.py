#@title preprocess, remove (remove duplicate cols,remove zero variance cols)
from sklearn.base import BaseEstimator 
import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder,OneHotEncoder
# from utils import _reverse_label_encoder
from sklearn.impute import SimpleImputer,KNNImputer
from sklearn.preprocessing import StandardScaler,MinMaxScaler,PowerTransformer,QuantileTransformer
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score,calinski_harabasz_score
from sklearn.pipeline import Pipeline
# from imblearn.over_sampling import SMOTE
# from imblearn.under_sampling import RandomUnderSampler
from kneed import KneeLocator
SKLEARN_EMPTY_STEP = "passthrough"
import logging

logging.basicConfig(level=logging.INFO)
# class InferDtypes():
#     # convdrting to float
    # def __init__(self,target) -> None:
        # self.target = target
    # def fit(self,dataset,y=None):
    #     data = dataset
    #     for i in data.select_dtypes(include=["object"]).columns:
    #         try:
    #             data[i] = data[i].astype("float32")
    #         except:
    #             None
#         #have str col names
#         data.columns = [str(i) for i in data.columns]
#         # remove special chars from col names
#         data.columns = data.columns.str.replace(r"[\,\}\{\]\[\:\"\']", "")
#         # if data type is bool or pandas Categorical , convert to categorical
#         # for i in data.select_dtypes(include=["bool", "category"]).columns:
#         #     data[i] = data[i].astype("object") 
#          # if int or float col has less than 5 unique vals convert to object: (exclude target)
#         for i in data.select_dtypes(include=["number"]).columns:
#             # if i != self.target:
#             if data[i].nunique() <= 5:  # hard coded
#                 data[i] = data[i].apply(str_if_not_null)
#             else:
#                 data[i] = data[i].astype("float32")
        # data.drop_duplicates(inplace=True)
        #         #infer datetime type
        #         for i in (
        #             data.select_dtypes(include=["object"]).columns
        #         ):
        #             try:
        #                 data[i] = pd.to_datetime(
        #                     data[i], infer_datetime_format=True, utc=False, errors="raise"
        #                 )
        #             except:
        #                 continue
        #         # drop datetime column
        #         data.drop(data.select_dtypes(include=["datetime64", "datetime64[ns, UTC]"]),axis=1,inplace=True)        
        # convert dtypes as of train data, le for target if classification prob,
        # for i in data.columns:
        #     data[i]=data[i].astype(self.final_dtypes[self.final_dtypes.index==i])
        
class Validation(BaseEstimator ):
    
    def __init__(self,target=None,ml_type='classification') -> None:
        self.ml_type=ml_type
        self.final_training_columns = []
        self.target = target
    def fit(self,dataset,y=None):
        logging.info("Preprocess step fit:Validation ")
        '''Performing filteration,drop target ->creates final col list'''
        
        data = dataset.drop(self.target,axis=1)
        data = data.loc[:,~data.columns.duplicated()]
        data.drop(data.select_dtypes(include=["datetime64", "datetime64[ns, UTC]"]),axis=1,inplace=True,errors='ignore')   
        print(data.columns)
        self.final_training_columns = data.columns.to_list()
        

    def fit_transform(self, dataset, y=None):
        logging.info("Preprocess step fit_transform:Validation ")
        '''For fit_transform include target'''
        data = dataset
        target_col = data[self.target]
        targetless_cols = data.drop(self.target,axis=1)
        self.fit(data)
        df=  pd.concat((self.transform(targetless_cols),target_col),axis=1)
        return df 

    def transform(self,dataset,y=None):
        '''For testing data, do filteration'''
        logging.info("Preprocess step transform:Validation ")
        data = dataset
        for i in self.final_training_columns:
            if i not in data.columns:
                raise TypeError(
                    f"test data does not have column {i} which was used for training."
                )
        # from fit_tranform
        data = data[self.final_training_columns]

        data.replace([np.inf, -np.inf], np.NaN, inplace=True)

        # drop id column---
        return data
       
# add iterative and knn imputer
class Imputation(BaseEstimator ):
    
    """
    required:num_strat,cat_strat
    Imputes null values for numeric and categorical with sklearn's Simple Impute
    Num strats: mean,median,most_frequent,zero
    Cat strats: most_frequent,others
    """
    def __init__(
        self,
        target=None,
        num_strat='mean',
        cat_strat='most_frequent',
        num_fill=0,
        cat_fill="others",
    ):
        self.target=target,
        self.num_strat = num_strat
        self.cat_strat = cat_strat
        self.num_impute = SimpleImputer(
            strategy=self.num_strat,
            fill_value=num_fill,
        )
        self.cat_impute = SimpleImputer(
            strategy=cat_strat,
            fill_value=cat_fill,
        )
        self.num_fill = num_fill
        self.cat_fill=cat_fill
        self.numeric_columns=[]
        self.categorical_columns=[]
    def fit(self, dataset, y=None):
        logging.info("Preprocess step fit:Inputation")
        data = dataset
        self.numeric_columns = data.drop((self.target)[0], axis=1).select_dtypes(include=["number"]).columns
        self.categorical_columns = data.drop((self.target)[0], axis=1).select_dtypes(include=["object"]).columns

        if len(self.numeric_columns) > 0:
            self.num_impute.fit(data[self.numeric_columns])
        if len(self.categorical_columns) >0:
            self.cat_impute.fit(data[self.categorical_columns])

    def transform(self, dataset, y=None):
        logging.info("Preprocess step transform:Inputation")
        data = dataset
        imputed_data = []
        if len(self.numeric_columns)>0:
            numeric_data = pd.DataFrame(
                self.num_impute.transform(data[self.numeric_columns]),
                columns=self.numeric_columns,
                index=data.index,
            )
            imputed_data.append(numeric_data)
        if len(self.categorical_columns)>0:
            categorical_data = pd.DataFrame(
                self.cat_impute.transform(data[self.categorical_columns]),
                columns=self.categorical_columns,
                index=data.index,
            )
            for col in categorical_data.columns:
                categorical_data[col] = categorical_data[col].apply(str)
            imputed_data.append(categorical_data)
        if imputed_data:
            data.update(pd.concat(imputed_data, axis=1))
        return data 

    def fit_transform(self,dataset,y=None):
        logging.info("Preprocess step fit_transform:Inputation")
        data = dataset
        target_col = data[(self.target)[0]]
        targetless_cols = dataset.drop((self.target)[0],axis=1)
        
        self.fit(data)
        df = pd.concat((self.transform(targetless_cols),target_col),axis=1)
        
        return df

class KnnImputation(BaseEstimator):
    pass

class IterativeImputation(BaseEstimator):
    pass

class ZeroVariance(BaseEstimator):
    def __init__(self,target=None) -> None:
        self.target=target
        self.col_drop = []
    def fit(self,dataset,y=None):
        '''For training data'''
        logging.info("Preprocess step fit:ZeroVariance")
        data = dataset.drop(self.target,axis=1)
        
        for i in data.select_dtypes(include=['number']).columns:
            if data[i].std()==0:
                self.col_drop.append(i)
       
    def transform(self,dataset,y=None):
        logging.info("Preprocess step transfomr:ZeroVariance")
        '''FOr testing data'''
        data= dataset.drop(self.col_drop,axis=1)
        return data
    def fit_transform(self,dataset,y=None):
        logging.info("Preprocess step fit_transform:ZeroVariance")
        data = dataset
        target_col = data[(self.target)]
        targetless_cols = data.drop(self.target,axis=1)
        self.fit(data)
        return pd.concat((self.transform(targetless_cols),target_col),axis=1)

class CatDummies(BaseEstimator):
    '''Cretes one hot encoding for categorical features '''
    def __init__(self,target=None):
        self.ohe = OneHotEncoder(dtype=np.float32,handle_unknown="ignore",)#
        self.target = target
        self.cols_to_drop = []
    def fit(self, dataset, y=None):      
        logging.info("Preprocess step fit:CatDummies")
        data = dataset.drop(self.target,axis=1)
        # will only do this if there are categorical variables
        if len(data.select_dtypes(include=("object")).columns) > 0:
            for i in data.select_dtypes(include=("object")).columns:
                # check for unique values
                if data[i].nunique() >= data.shape[0]:
                    self.cols_to_drop.append(i)
                    data = data.drop(i,axis=1,errors='ignore')
            self.data_nonc = data.select_dtypes(exclude=("object"))
            categorical_data = data.select_dtypes(include=("object"))
            # # now fit the trainin column
            self.ohe.fit(categorical_data)
            self.data_columns = self.ohe.get_feature_names(categorical_data.columns)

    def transform(self, dataset, y=None):
        logging.info("Preprocess step transform:CatDummies")
        data = dataset
        # will only do this if there are categorical variables
        if len(data.select_dtypes(include=("object")).columns) > 0:
            if len(self.cols_to_drop) >=1:
                data = data.drop(self.cols_to_drop,axis=1,errors='ignore')
            # only for test data
            self.data_nonc = data.select_dtypes(exclude=("object"))
            # fit only categorical columns
            array = self.ohe.transform(
                data.select_dtypes(
                    include=("object")
                )
            ).toarray()
            data_dummies = pd.DataFrame(array, columns=self.data_columns)
            data_dummies.index = self.data_nonc.index
            
            # now put target , numerical and categorical variables back togather
            data = pd.concat(( self.data_nonc, data_dummies), axis=1)
            del self.data_nonc
            return data
        else:
            return data
    def fit_transform(self, dataset, y=None):
        logging.info("Preprocess step fit_transform:CatDummies")
        data = dataset
        target_col = data[self.target]
        targetless_cols = data.drop(self.target,axis=1)
        self.fit(data)
        return pd.concat((self.transform(targetless_cols),target_col),axis=1)

class ScaleTransformer(BaseEstimator):
    '''Applies, minmax,zscore,yeo-johnson, quantile'''
    def __init__(self,target=None,function ='zscore') -> None:
        self.function = function
        self.target = target
        
    def fit(self,dataset,y=None):
        '''For training data, apply transformation'''
        logging.info("Preprocess step fit:ScaleTransformer")
        data = dataset.drop(self.target,axis=1)
        self.num_cols = data.select_dtypes(include=['number']).columns
        
        if len(self.num_cols)>0:
          
          if self.function=='zscore':
            self.scaler = StandardScaler()
          elif self.function =='minmax':
            self.scaler = MinMaxScaler()
          elif self.function =='yeo-johnson':
            self.scaler = PowerTransformer(method="yeo-johnson", standardize=True)
          elif self.function =='quantile':
            self.scaler =QuantileTransformer(output_distribution="normal",random_state=45)
        self.scaler.fit(data[self.num_cols])
        
    
    def transform(self,dataset,y=None):
        '''FOr testing data, apply transformer used in training'''
        logging.info("Preprocess step transform:ScaleTransformer")

        data = dataset
        # len of num cols is >0
        if len(self.num_cols)>0:
            num_data = pd.DataFrame(self.scaler.transform(data[self.num_cols]))
            num_data.index = data.index
            num_data.columns = self.num_cols
            for i in self.num_cols:
                data[i] = num_data[i]
        
        return data
    
    def fit_transform(self,dataset,y=None):
        logging.info("Preprocess step fit_transform:ScaleTransformer")

        data = dataset
        
        target_col = data[self.target]
        
        targetless_cols = data.drop(self.target,axis=1)
        self.fit(data)
        c = pd.concat((self.transform(targetless_cols),target_col),axis=1)
        
        return c

class OutlierRemoval(BaseEstimator):
    pass

class PerfectCollinearity(BaseEstimator):
    '''Removes first column which have perfect i.e, 1 collinearity between them(features)
       One hot encoded variables only
    '''
    def __init__(self,target=None) -> None:
        self.col_drop = []
        self.target = target
    def fit(self,dataset,y=None):
        logging.info("Preprocess step fit:PerfectCollinearity")

        data = dataset.drop(self.target,axis=1)
        if len(data.columns) <= 2:
            return data
        corr = pd.DataFrame(np.corrcoef(data.T))
        corr.columns = data.columns
        corr.index = data.columns
        corr_matrix = abs(corr)

        # Now, add a column for variable name and drop index
        corr_matrix["column"] = corr_matrix.index
        corr_matrix.reset_index(drop=True, inplace=True)

        # now we need to melt it , so that we can correlation pair wise , with two columns
        cols = corr_matrix.column
        melt = corr_matrix.melt(id_vars=["column"], value_vars=cols).sort_values(
            by="value", ascending=False
        )  # .dropna()
        melt["value"] = round(melt["value"], 2)  # round it to two digits

        # now pick variables where value is one and 'column' != variabe ( both columns are not same)
        c1 = melt["value"] == 1.00
        c2 = melt["column"] != melt["variable"]
        melt = melt[((c1 == True) & (c2 == True))]

        # we need to now eleminate all the pairs that are actually duplicate e.g cor(x,y) = cor(y,x) , they are the same , we need to find these and drop them
        melt["all_columns"] = melt["column"] + melt["variable"]

        # this puts all the coresponding pairs of features togather , so that we can only take one, since they are just the duplicates
        melt["all_columns"] = [sorted(i) for i in melt["all_columns"]]

        # # now sort by new column
        melt = melt.sort_values(by="all_columns")

        # # take every second colums
        melt = melt.iloc[::2, :]

        # lets keep the columns on the left hand side of the table
        self.col_drop = melt["variable"]

    def transform(self,dataset,y=None):
        logging.info("Preprocess step transform:PerfectCollinearity")

        return dataset.drop(self.col_drop,axis=1)
    def fit_transform(self, dataset, y=None):
        logging.info("Preprocess step fit_transform:PerfectCollinearity")

        data = dataset
        target_col = data[self.target]
        targetless_cols = data.drop(self.target,axis=1)
        self.fit(data)
        return pd.concat((self.transform(targetless_cols),target_col),axis=1)


class ClusterData(BaseEstimator):
    def __init__(self,target=None) -> None:
        '''Create cluster for data (min:2,max:20)'''
        self.target = target
        # self.n_clusters = 3 #change to sqrt 
    def fit(self,dataset,y=None):
        logging.info("Preprocess step fit:ClusterData")
        wcss = []
        data = dataset.drop(self.target,axis=1,errors='ignore')
        print("-----------------Fit cluster data:",data.shape)
        # for i in range (2,10):  #hard coded
        #     kmeans=KMeans(n_clusters=i,init='k-means++',random_state=42) # initializing the KMeans object
        #     kmeans.fit(data) # fitting the data to the KMeans Algorithm
        #     wcss.append(kmeans.inertia_)
        # self.kn = KneeLocator(range(1, 10), wcss, curve='convex', direction='decreasing')
        self.kmeans = KMeans(n_clusters=5,init='k-means++',random_state=42)
        self.kmeans.fit(data)

    def transform(self,dataset,y=None):
        logging.info("Preprocess step transform:ClusterData")
        data = dataset
        data['cluster_label']=self.kmeans.predict(data)
        return data
    def fit_transform(self,dataset,y=None):
        logging.info("Preprocess step fit_transfomrm:ClusterData")
        data = dataset
        target_col = data[(self.target)]
        targetless_cols = data.drop(self.target,axis=1)
        self.fit(data)
        return pd.concat((self.transform(targetless_cols),target_col),axis=1)

class FeatureSelection(BaseEstimator):
    pass

class Multicollinearity(BaseEstimator):
    pass

class ImbalancedData(BaseEstimator):
    pass
    # over = SMOTE(sampling_strategy=0.1)
    # under = RandomUnderSampler(sampling_strategy=0.5)
    # steps = [('o', over), ('u', under)]
    # pipeline = Pipeline(steps=steps)

    # # transform the dataset
    # X, y = pipeline.fit_resample(data.drop(self.target,axis=1),self.target)

class TargetTreat(BaseEstimator):
    def __init__(self,target=None,ml_type='classification') -> None:
        self.target = target
        self.ml_type = ml_type
        self.le = LabelEncoder()
    def fit(self,dataset,y=None):
        logging.info("Preprocess step fit:TargetTreat")
        data = dataset
        if ((self.target !=None) and (data[(self.target)].dtypes=='object')):
        # remove row where target is NaN
            try:
                logging.warning((data[self.target].isnull().sum()))
                data.dropna(subset=[self.target], inplace=True)
                logging.warning("Found nan rows in target")
                
                self.le.fit(data[self.target])
                self.replacement = _get_labelencoder_reverse_dict(self.le)
            except KeyError:
                pass
            
            except Exception as e:
                print(e)
                raise e
    def transform(self,dataset,y=None):
        logging.info("Preprocess step transform:TargetTreat")
        data = dataset
        if (self.target) in data.columns:
            try:
                data.dropna(subset=[self.target], inplace=True)
            except KeyError:
                pass
            if (data[self.target].dtypes=='object'):
                data[self.target] = self.le.transform(data[self.target])      
        return data
    def fit_transform(self,dataset,y=None):
        logging.info("Preprocess step fit_transform:TargetTreat")
        self.fit(dataset)                
        return self.transform(dataset)

def _get_labelencoder_reverse_dict(le: LabelEncoder) -> dict:
    # now get the replacement dict
    rev = le.inverse_transform(range(0, len(le.classes_)))
    rep = np.array(range(0, len(le.classes_)))
    replacement = {}
    for i, k in zip(rev, rep):
        replacement[i] = k
    return replacement

def preprocess_path(ml_type,
scale_data=True,
scaling_method="zscore",
numeric_imputation_strategy="mean",
dummify_categoricals=True,
remove_perfect_collinearity=False,
target=None,data=None,
cluster_entire_data=False,zerovar=True):
   
    validates = Validation(
        ml_type=ml_type,
        target=target,
    )
    imputer = Imputation(
        target=target
    )
    if scale_data == True:
        scaling = ScaleTransformer(
            target=target,
            function=scaling_method,
        )
    else:
        scaling = SKLEARN_EMPTY_STEP
    
    if dummify_categoricals == True:
        dummy = CatDummies(target =target)
    else:
        dummy = SKLEARN_EMPTY_STEP

    if cluster_entire_data == True:
        cluster_all = ClusterData(
            target = target
        )
    else:
        cluster_all = SKLEARN_EMPTY_STEP
    if remove_perfect_collinearity == True:
        fix_perfect = PerfectCollinearity(target=target)
    else:
        fix_perfect = SKLEARN_EMPTY_STEP
    if zerovar==True:
        zerovar = ZeroVariance(target=target)
    else:
        zerovar = SKLEARN_EMPTY_STEP
    target_treat = TargetTreat(target=target,ml_type=ml_type)
    pipe = Pipeline(
         [   
            ("validates", validates),
            ("zerovar",zerovar),
            ("imputer", imputer),
            ("dummy", dummy),
            ("scaling", scaling),
            ("fix_perfect", fix_perfect),
            
            ("cluster_all", cluster_all),
            ("target_treat",target_treat),
            
        ]
    )    
    return pipe

