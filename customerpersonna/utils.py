import pandas as pd


def order_cluster(cluster_field_name, target_field_name,df,ascending):
    '''Changing labels to be set as in lower label for higher cluster mean for rfm score later'''
    new_cluster_field_name = 'new_' + cluster_field_name
    df_new = df.groupby(cluster_field_name)[target_field_name].mean().reset_index()
    df_new = df_new.sort_values(by=target_field_name,ascending=ascending).reset_index(drop=True)
    df_new['index'] = df_new.index
    df_final = pd.merge(df,df_new[[cluster_field_name,'index']], on=cluster_field_name)
    df_final = df_final.drop([cluster_field_name],axis=1)
    df_final = df_final.rename(columns={"index":cluster_field_name})
    return df_final

def read_corr_df(path):
        ext = path.split('.')[-1]
        data = None
        if ext=='csv':
            data = pd.read_csv(path)
        elif ext =='h5':
            data = pd.read_hdf(path) 
        elif ext == 'xlx':
            data = pd.read_excel(path)
        elif ext == 'parquet':
            data = pd.read_parquet(path)
        elif ext == 'sql':
            data = pd.read_sql(path)
        elif ext == 'json':
            data = pd.read_json(path)
        elif ext == 'html':
            data = pd.read_html(path)
        else:
            raise TypeError("File must have one of these ext: csv,h5,xlx,parquet,sql,json,html")
            # return {'status':False,'Message':'Unsupported Type'}
        return data
    