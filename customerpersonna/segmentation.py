from sklearn_extra.cluster import KMedoids
from customerpersonna.utils import order_cluster
import numpy as np
def rfm_segment(rfm_df,recency,frequency,monetary):
    '''RFM segmentation usign quantiles'''
    rfm_df['R_rank'] = rfm_df[recency].rank(ascending=False)
    rfm_df['F_rank'] = rfm_df[frequency].rank(ascending=True)
    rfm_df['M_rank'] = rfm_df[monetary].rank(ascending=True)

    # normalizing the rank of the customers
    rfm_df['R_rank_norm'] = (rfm_df['R_rank']/rfm_df['R_rank'].max())*100
    rfm_df['F_rank_norm'] = (rfm_df['F_rank']/rfm_df['F_rank'].max())*100
    rfm_df['M_rank_norm'] = (rfm_df['F_rank']/rfm_df['M_rank'].max())*100


    rfm_df['RFM_Score'] = 0.15*rfm_df['R_rank_norm']+0.28 * rfm_df['F_rank_norm']+0.57*rfm_df['M_rank_norm']
    rfm_df['RFM_Score'] *= 0.05
    rfm_df = rfm_df.round(2)
    # rfm_df[['cust_id', 'RFM_Score']].head(7)
    rfm_df["score_label"] = np.where(rfm_df['RFM_Score'] >=
									4.5, "Champion",
									(np.where(
										rfm_df['RFM_Score'] > 4,
										"Potential loyalist",
										(np.where(
	rfm_df['RFM_Score'] > 3,
							"Need attention",
							np.where(rfm_df['RFM_Score'] > 1.6,
							'At risk', 'Lost'))))))
    rfm_df.drop(columns=['R_rank', 'F_rank', 'M_rank','R_rank_norm','F_rank_norm','M_rank_norm'], inplace=True)
    return rfm_df


def ml_segment(rfm_df,recency,frequency,monetary,k=5):
    #Step 1 : Clusters for Recency
    kmedoids = KMedoids(n_clusters=5, random_state=0, max_iter=1000,init='k-medoids++',metric='euclidean').fit(rfm_df[[recency]])
    rfm_df["ml_label_r"] = kmedoids.predict(rfm_df[[recency]])
    rfm_df = order_cluster('ml_label_r', recency,rfm_df,False)
    
    #Step 2 : Clusters for Frequency
    kmedoids = KMedoids(n_clusters=5, random_state=0, max_iter=1000,init='k-medoids++',metric='euclidean').fit(rfm_df[[frequency]])
    rfm_df['ml_label_f'] = kmedoids.predict(rfm_df[[frequency]])
    rfm_df = order_cluster('ml_label_f', frequency,rfm_df,True)

    #Step 3 : Clusters for Monetary
    kmedoids = KMedoids(n_clusters=5, random_state=0, max_iter=1000,init='k-medoids++',metric='euclidean').fit(rfm_df[[monetary]])
    rfm_df['ml_label_m'] = kmedoids.predict(rfm_df[[monetary]])
    rfm_df = order_cluster('ml_label_m', monetary,rfm_df,True)
    rfm_df['ml_label'] = rfm_df['ml_label_r'].astype(str)+rfm_df['ml_label_f'].astype(str)+rfm_df['ml_label_m'].astype(str)
    rfm_df.drop(['ml_label_r','ml_label_f','ml_label_m'],axis=1,inplace=True)
    segt_map = {
    r'30.': 'Promising',
    r'23.': 'Loyal',
    r'24.': 'Loyal',
    r'33.': 'Loyal',
    r'34.': 'Loyal',
    r'43.': 'Loyal',
    r'32.': 'Potential loyalist',
    r'31.': 'Potential loyalist',
    r'42.': 'Potential loyalist',
    r'41.': 'Potential loyalist',
    r'21.': 'Need attention',
    r'22.': 'Need attention',
    r'12.': 'Need attention',
    r'11.': 'Need attention',
    r'40.': 'New',
    r'20.': 'About to sleep',
    r'14.': 'Cant loose them',
    r'04.': 'Cant loose them',
    r'10.': 'Lost',
    r'00.': 'Lost',
    r'01.': 'Lost',
    r'02.': 'At risk',
    r'03.': 'At risk',
    r'13.': 'At risk',
    r'44.': 'Champion',
    }

    rfm_df['ml_label'] = rfm_df['ml_label'].replace(segt_map, regex=True)

    return rfm_df
    