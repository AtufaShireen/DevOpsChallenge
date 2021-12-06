
from automl.models import getregression,getclassification
from joblib import load,dump
import pandas as pd
from sklearn.model_selection import train_test_split,StratifiedKFold
from sklearn.metrics import f1_score,precision_score,recall_score,accuracy_score
from sklearn.metrics import mean_absolute_error,mean_squared_error
from xgboost import XGBClassifier
from automl.preprocessing.preprocessor import preprocess_path
from automl.models.basemodels.ensemblers import BaseXGBClassifier
from automl.models.utils import get_best_param
from automl.models.mlalgos.ensemble import BoostingEnsemble
from sklearn.base import clone
##-------------------------Classification Problem---------------------------#
path_1 = r'C:\Users\anony\Projects\AUTOMLOPS\ValidationProcess\TRAIN\GOODRAWDATA\de32b12f-bdc3-4db5-984d-7c2a3ed03096\754d0fb8-125c-4658-97e6-4d78708eae67\forestcover_28011994_120214.h5'
path_2 = r'C:\Users\anony\Projects\AUTOMLOPS\ValidationProcess\TRAIN\GOODRAWDATA\de32b12f-bdc3-4db5-984d-7c2a3ed03096\754d0fb8-125c-4658-97e6-4d78708eae67\forestcover_28011999_120259.h5'
df_1 = pd.read_hdf(path_1)
df_2 = pd.read_hdf(path_2)
df = pd.concat([df_1,df_2],axis=0)
target = 'class'

# tune_grid = BaseXGBClassifier().tune_grid
# print(tune_grid)
# preprocess_pipe = preprocess_path(data=df,ml_type='classification',scale_data=True,scaling_method="minmax",
#     target=target,dummify_categoricals=True,cluster_entire_data=False)

# data_ = preprocess_pipe.fit_transform(df)
# print(data_.head())
# x_train,x_test,y_train,y_test = train_test_split(data_.drop(target,axis=1),data_[target],test_size=0.20,stratify=data_[target],random_state=45)

# model = BoostingEnsemble(x_train,y_train,ml_type='classification')
# v = clone(BaseXGBClassifier().class_def)
# model= v.set_params(n_jobs=-1,    
#                     use_label_encoder=False,
#                     objective="multi:softmax",
#                     eval_metric="merror",
#                     verbosity=0,
#                     num_class=len(set(y_train)))
model = getclassification.BestClassificationModel(data=df,target=target)
# a,b = get_best_param(model,tune_grid,df.drop(target,axis=1),df[target])
# print(a,b)

# print(df.head())               
model.fit()
# model.fit(x_train,y_train)
predictions = (model.predict(df))
print(accuracy_score(df[target],predictions))

# x_train,x_test,y_train,y_test = train_test_split(df.drop(target,axis=1),df[target],test_size=0.02,stratify=df[target],random_state=45)
# train_df = pd.concat([x_train,y_train],axis=1)
# test_df = pd.concat([x_test,y_test],axis=1)

##---------------------------Training-------------------------------#
# basemodel = getclassification.BestClassificationModel(df,target)
# basemodel.fit() #fits to best model
# dump(basemodel.preprocess_pipe,'classif_preprocess_pipe.joblib')
# metrics = basemodel.scores_grid
# print(metrics)
# dump(basemodel,'best-classif-model.joblib')
# dump(metrics,'classif-metrics.joblib')

# #---------------------------Testing---------------------------------#
# pipe = load('classif_preprocess_pipe.joblib')
# model = load('best-classif-model.joblib')
# print(model.max_model.modelname)
# print(model.max_model.get_params())
# predictions = model.predict(df.drop(target,axis=1))
# predictions = model.get_inverse_label(predictions)
# # #-------------------------Score-------------------------------------#
# n_df = pd.DataFrame(list(zip(predictions,df[target])),columns=['predicts','actual'])
# n_df['predicts'] = n_df['predicts'].apply(lambda x: 1 if x=='Yes' else 0)
# n_df['actual'] = n_df['actual'].apply(lambda x: 1 if x=='Yes' else 0)
# print(n_df.head())
# # print('CORRECT:',model.score(n_df['actual'],n_df['predicts'],normalize=False),"TOTAL:",len(n_df['actual']))
# print('SCORE:',accuracy_score(n_df['actual'],n_df['predicts']))


##------------------------------Regression Problem--------------------#

# df = pd.read_csv('house_price.csv',nrows=50)
# print(df.shape[0])
# target = 'TARGET(PRICE_IN_LACS)'
# x_train,x_test,y_train,y_test = train_test_split(df.drop(target,axis=1),df[target],test_size=0.2,random_state=45)
# train_df = pd.concat([x_train,y_train],axis=1)
# test_df = pd.concat([x_test,y_test],axis=1)

# # #---------------------------Training-------------------------------#
# basemodel = getregression.BestRegessionModel(train_df,target)
# basemodel.fit() #fits to best model
# dump(basemodel.preprocess_pipe,'regress_preprocess_pipe.joblib')
# metrics = basemodel.scores_grid
# dump(basemodel,'best-regress-model.joblib')
# dump(metrics,'regress-metrics.joblib')
# print(metrics)
# ##---------------------------Testing---------------------------------#
# # pipey = load('preprocess_pipe.joblib')
# model = load('best-regress-model.joblib')
# predictions = basemodel.predict(x_train)
# ##-------------------------Score-------------------------------------#
# n_df = pd.DataFrame(list(zip(predictions,y_train)),columns=['predicts','actual'])
# print(n_df.head())
# print('SCORE:',mean_squared_error(n_df['actual'],n_df['predicts'],squared=False))
# print(basemodel.scores_grid)
