import pandas as pd
def csv_to_h5(csv_file_path,h5_file_path):
    hdf_key = 'hdf_key'
    store = pd.HDFStore(h5_file_path)
    print('H5 File created for users: ')
    
    for chunk in pd.read_csv(csv_file_path,iterator=True, chunksize=50):
        store.append(hdf_key, chunk, index=False)
    # store.create_table_index(hdf_key, optlevel=9, kind='full')
    store.close()
    print('H5 File operation Done: ')