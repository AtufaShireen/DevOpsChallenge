import pandas as pd

d = {'standalone': {'r2': 0.5736590813365772, 'mae': 6.48560606060606, 'mse': 71.88126304713806, 'rmse': 8.478281845228906},
 'boost': {'r2': 0.8193064763353013, 'mae': 3.9755439446189182, 'mse': 30.46500614150597, 'rmse': 5.519511404237332},
 'bag': {'r2': 0.633229215079345, 'mae': 6.257165498105025, 'mse': 61.83771276643529, 'rmse': 7.863695871944393}}

df = pd.DataFrame(d,columns=['standalone','boost','bag'])
print(df.head())
test = {	"SampleFileName": "cement_strength_08012020_120000.csv",
	"LengthOfDateStampInFile": 8,
	"LengthOfTimeStampInFile": 6,
	"NumberofColumns" : 8,
	"ColName": {
	"Cement_component_1" : "FLOAT",
		"Blast_Furnace_Slag_component_2" : "FLOAT",
		"Fly_Ash_component_3" : "FLOAT",
		"Water_component_4" : "FLOAT",
		"Superplasticizer_component_5" : "FLOAT",
		"Coarse_Aggregate_component_6" : "FLOAT",
		"Fine_Aggregate_component_7" : "FLOAT",
		"Age_day" : "INTEGER"
	}
}

train = {	"SampleFileName": "cement_strength_08012020_120000.csv",
	"LengthOfDateStampInFile": 8,
	"LengthOfTimeStampInFile": 6,
	"NumberofColumns" : 9,
	"ColName": {
		"Cement_component_1" : "FLOAT",
		"Blast_Furnace_Slag_component_2" : "FLOAT",
		"Fly_Ash_component_3" : "FLOAT",
		"Water_component_4" : "FLOAT",
		"Superplasticizer_component_5" : "FLOAT",
		"Coarse_Aggregate_component_6" : "FLOAT",
		"Fine_Aggregate_component_7" : "FLOAT",
		"Age_day" : "INTEGER",
		"Concrete_compressive_strength" : "FLOAT"
	},
    "Target":"Concrete_compressive_strength"
}
# new = {
#     "SampleFileName": "forestcover_28011992_120212.csv",
# 	"LengthOfDateStampInFile": 8,
# 	"LengthOfTimeStampInFile": 6,
# 	"NumberofColumns" : 32,
#     "ColName": {
#         "ID":"Float",
#         "Year_Birth":"Float",
#          "Education":"String",
#           "Marital_Status":"String",
#            "Income":"Float",
#             "Kidhome":"Float",
#         "Teenhome":"Float",
#          "Dt_Customer":"Float",
#           "Recency":"Float",
#            "MntWines":"Float",
#             "MntFruits":"Float",
#         "MntMeatProducts":"Float",
#          "MntFishProducts":"Float", 
#          "MntSweetProducts":"Float",
#         "MntGoldProds":"Float",
#          "NumDealsPurchases":"Float",
#           "NumWebPurchases":"Float",
#         "NumCatalogPurchases":"Float",
#          "NumStorePurchases":"Float",
#           "NumWebVisitsMonth":"Float",
#         "AcceptedCmp3":"Float",
#          "AcceptedCmp4":"Float",
#           "AcceptedCmp5":"Float", 
#           "AcceptedCmp1":"Float",
#         "AcceptedCmp2":"Float",
#          "Complain":"Float", 
#          "Z_CostContact":"Float",
#           "Z_Revenue":"Float",
#            "Response":"Float",
#         "spent_total":"Float", 
#         "Frequency":"Float",
#          "Age":"Float"
# },
#     "RFMCols":{
#         "id_col":"ID",
#         "monetary_col":"spent_total",
#         "trans_date_col":"Dt_Customer",
#         "recency_col":"Recency",
#         "frequency_col":"Frequency",
#         "age_col":"Age"
#     }
# }



# import os,json
# from automl.models import getclassification
# file = r"C:\Users\anony\Projects\AUTOMLOPS\ValidationProcess\TRAIN\FINALDATA\de32b12f-bdc3-4db5-984d-7c2a3ed03096\998c5a9e-d29c-48e9-b2a9-b60e01407098\forestcover-train.csv"
# data = pd.read_csv(file)
# target = 'class'
# model = getclassification.BestClassificationModel(data,target)
# model.fit()
# print(model.scores_grid)
# from sklearn.metrics import r2_score
# v = json.load(new)
# print(len(new["ColName"]))
# k = r'C:\Users\anony\Downloads\cement_train'
# for i in os.listdir(k):
    # print(i)
# i = 'cementstrength_08012020_120021.csv'
# x = pd.read_csv(f'{k}\{i}')
# target = "Concrete_compressive_strength"
# model = getregression.BestRegessionModel(data=x,target=target)
# model.fit()
# preds = model.predict(x.drop(target,axis=1))
# print(r2_score(x[target],preds))
# print(len(x.columns),len(test['ColName'].keys()))
# x.columns = [i for i in test['ColName'].keys()]
# i = i.replace('cement_strength','cementstrength')
# x.to_csv(f'{k}',index=False)