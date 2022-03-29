from lifetimes import GammaGammaFitter,BetaGeoFitter
import pandas as pd
def fit_clv_model(df,rec_col,freq_col,mon_col,age_col):
    rfm_df = df[df[freq_col]>1]
    rfm_df = rfm_df[rfm_df[mon_col]>0]
    bgf = BetaGeoFitter(penalizer_coef=0.001)
    bgf.fit(rfm_df[freq_col], rfm_df[rec_col], rfm_df[age_col])
    ggf = GammaGammaFitter(penalizer_coef=0.001)
    ggf.fit(frequency = rfm_df[freq_col], monetary_value = rfm_df[mon_col])
    return (bgf,ggf)

def predict_purchase(bgf,ggf,rfm_df,rec_col,freq_col,mon_col,age_col,discount_rate=None,time=None,expected_purchases_date=None):

    t = expected_purchases_date if expected_purchases_date!=None else 1 # to calculate the number of expected repeat purchases over the next 30 days
    new_df = pd.DataFrame()
    new_df['predicted_purchases'] = bgf.conditional_expected_number_of_purchases_up_to_time(t, rfm_df[freq_col], rfm_df[rec_col], rfm_df[age_col])
    new_df['p_alive'] = bgf.conditional_probability_alive(rfm_df[freq_col], rfm_df[rec_col], rfm_df[age_col])
    new_df['predicted_sales'] = ggf.conditional_expected_average_profit(rfm_df[freq_col], rfm_df[mon_col])
    discount_rate = discount_rate if discount_rate!=None else 0.01
    time = time if time!=None else 12
    new_df['LTV'] = ggf.customer_lifetime_value(bgf,rfm_df[freq_col], rfm_df[rec_col], rfm_df[age_col], rfm_df[mon_col],
    time = 12,freq='D',discount_rate =discount_rate)
    new_df['cust_id'] = rfm_df['cust_id']

    return new_df
