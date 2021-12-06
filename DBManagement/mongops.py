import pymongo
import pandas as pd
import json
import os
# from ProjectLoggings.loggs import *
class MongoDBmanagement:

    def __init__(self,user_id=None,project_id=None):
        # from ProjectLoggings import loggs
        '''setting the required url'''
        
        try:
            self.username = str(os.environ.get('MONGO_USERNAME'))
            self.password = str(os.environ.get('MONGO_PASSWORD'))
            # self.url = f"mongodb+srv://{self.username}:{self.password}@cluster0.3hvrs.mongodb.net/myFirstDatabase?retryWrites=true&w=majority"
            self.url = "mongodb://localhost:27017/"
            self.mongo_client = pymongo.MongoClient(self.url)
            self._user_id = user_id
            self._project_id = project_id
        except Exception as e:
            raise Exception("At __init__:",e)
    
    @property
    def user_id(self):
        return self._user_id

    @user_id.setter
    def user_id(self, value):
        self._user_id = value
    
    @property
    def project_id(self):
        return self._project_id

    @project_id.setter
    def project_id(self, value):
        self._project_id = value
    
    def getMongoDBClientObject(self):
        
        '''creating a client object for connection'''

        try:
            # project_logs("Getting Connected",user_id=self.user_id,project_id=self.project_id)
            mongo_client = self.mongo_client
            return mongo_client
        except Exception as e:
            # project_logs(f"At getMongoDBClientObject:{e}",user_id=self.user_id,project_id=self.project_id,exception=True)
            raise Exception("At getMongoDBClientObject:",e)

    def closeMongoDBconnection(self,mongo_client):
        '''Closing connec of client'''
        
        try:
            # project_logs("Closing Connection",user_id=self.user_id,project_id=self.project_id)
            mongo_client.close()
        except Exception as e:
            # project_logs(f"At closeMongoDBconnection:{e}",user_id=self.user_id,project_id=self.project_id,exception=True)
            raise Exception("At closeMongoDBconnection:",e)

    def isDatabasePresent(self,db_name):
        '''Check if database is already present'''
        
        x = self.getMongoDBClientObject()
        try:
            # project_logs("Cheking for DB",user_id=self.user_id,project_id=self.project_id)
            for db in x.list_database_names():
                
                if db_name == db :
                    self.closeMongoDBconnection(x)
                    return True
            self.closeMongoDBconnection(x)
            return False
        except Exception as e:
            # project_logs(f"At isDatabasePresent:{e}",user_id=self.user_id,project_id=self.project_id,exception=True)
            raise Exception("At isDatabasePresent: ",e)
    
    def createDatabase(self,db_name):
        '''Create Database for client'''
        
        try:
            # project_logs("Creating database",user_id=self.user_id,project_id=self.project_id)
            client = self.getMongoDBClientObject()
            database_check_status = self.isDatabasePresent(db_name)
            if not database_check_status:
                database = client[db_name]
                client.close()
                return database
            else:
                database = client[db_name]
                client.close()
                return database
        except Exception as e:
            # project_logs(f"At createDatabase: {e}",user_id=self.user_id,project_id=self.project_id,exception=True)
            raise Exception("At CreateDatabase: ",e)
    

    def dropDatabase(self, db_name):
        """
        This function deletes the database from MongoDB
        :param db_name:
        :return:
        """
        
        try:
            # project_logs("dropping database",user_id=self.user_id,project_id=self.project_id)
            client = self.getMongoDBClientObject()
            client.drop_database(db_name)
            client.close()
            return True
        except Exception as e:
            # project_logs(f"At dropDatabase: {e}",user_id=self.user_id,project_id=self.project_id,exception=True)
            raise Exception(f"(dropDatabase): Failed to delete database {db_name}\n" + str(e))
    
    def listDatabase(self):
        """
        This returns databases.
        """
        
        try:
            # project_logs("getting database list ",user_id=self.user_id,project_id=self.project_id)
            client = self.getMongoDBClientObject()
            return client.list_database_names
        except Exception as e:
            # project_logs(f"At listDatabase: {e}",user_id=self.user_id,project_id=self.project_id,exception=True)
            raise Exception(f"(getDatabase): Failed to get the database list",e)

    def getDatabase(self, db_name):
        """
        This returns databases.
        """
        
        try:
            # project_logs("getting database ",user_id=self.user_id,project_id=self.project_id)
            client = self.getMongoDBClientObject()
            return client[db_name]
        except Exception as e:
            # project_logs(f"At getDatabase: {e}",user_id=self.user_id,project_id=self.project_id,exception=True)
            raise Exception(f"(getDatabase): Failed to get the database list",e)
    
    def getCollection(self, collection_name, db_name):
        """
        This returns collection.
        :return:
        """
        
        try:
            # project_logs("getting collection",user_id=self.user_id,project_id=self.project_id)
            database = self.getDatabase(db_name)
            return database[collection_name]
        except Exception as e:
            # project_logs(f"At getCollection: {e}",user_id=self.user_id,project_id=self.project_id,exception=True)
            raise Exception(f"(getCollection): Failed to get the database list.",e)
    
    def isCollectionPresent(self, collection_name, db_name):
        """
        This checks if collection is present or not.
        :param collection_name:
        :param db_name:
        :return:
        """
        
        try:
            # project_logs("Cheking for collection",user_id=self.user_id,project_id=self.project_id)
            database_status = self.isDatabasePresent(db_name=db_name)
            if database_status:
                database = self.getDatabase(db_name=db_name)
                for col in database.list_collection_names():
                    if col == collection_name :
                        return True
                return False
            else:
                return False
        except Exception as e:
            # project_logs(f"At isCollectionPresent: {e}",user_id=self.user_id,project_id=self.project_id,exception=True)
            raise Exception(f"(isCollectionPresent): Failed to check collection\n" + str(e))
    
    def createCollection(self, collection_name, db_name):
        """
        This function creates the collection in the database given.
        :param collection_name:
        :param db_name:
        :return:
        """
        
        try:
            # project_logs("creating collection",user_id=self.user_id,project_id=self.project_id)
            collection_check_status = self.isCollectionPresent(collection_name=collection_name, db_name=db_name)
            if not collection_check_status:
                database = self.getDatabase(db_name=db_name)
                collection = database[collection_name]
                return collection
        except Exception as e:
            # project_logs(f"At createCollection: {e}",user_id=self.user_id,project_id=self.project_id,exception=TRue)
            raise Exception(f"(createCollection): Failed to create collection {collection_name}\n" + str(e))
    
    def dropCollection(self, collection_name, db_name):
        """
        This function drops the collection
        :param collection_name:
        :param db_name:
        :return:
        """
        # project_logs("dropping collection",user_id=self.user_id,project_id=self.project_id)
        try:
            collection_check_status = self.isCollectionPresent(collection_name=collection_name, db_name=db_name)
            if collection_check_status:
                collection = self.getCollection(collection_name=collection_name, db_name=db_name)
                collection.drop()
                return True
            else:
                return False
        except Exception as e:
            # project_logs(f"At dropCollection: {e}",user_id=self.user_id,project_id=self.project_id)
            raise Exception(f"(dropCollection): Failed to drop collection {collection_name}")
    
    def InsertRecord(self, db_name, collection_name, record):
        """
        This inserts a record.
        :param db_name:
        :param collection_name:
        :param record:
        :return:
        """
        # project_logs("Inserting Record",user_id=self.user_id,project_id=self.project_id)
        try:
            # collection_check_status = self.isCollectionPresent(collection_name=collection_name,db_name=db_name)
            # print(collection_check_status)
            # if collection_check_status:
            collection = self.getCollection(collection_name=collection_name, db_name=db_name)
            collection.insert_one(record)
            return True
        except Exception as e:
            # project_logs(f"At InsertRecord: {e}",user_id=self.user_id,project_id=self.project_id,exception=True)
            raise Exception(f"(insertRecords): Something went wrong on inserting record\n" + str(e))

    def findfirstRecord(self, db_name, collection_name,query=None):
        """
        """
        # project_logs("getting first record",user_id=self.user_id,project_id=self.project_id)
        try:
            collection_check_status = self.isCollectionPresent(collection_name=collection_name, db_name=db_name)
            if collection_check_status:
                collection = self.getCollection(collection_name=collection_name, db_name=db_name)
     
                firstRecord = collection.find_one(query)
                return firstRecord
        except Exception as e:
            # project_logs(f"At findfirstRecord: {e}",user_id=self.user_id,project_id=self.project_id,exception=True)
            raise Exception(f"(findRecord): Failed to find record for the given collection and database\n" + str(e))

    def findAllRecords(self, db_name, collection_name):
        """
        """
        # project_logs("gettign all records",user_id=self.user_id,project_id=self.project_id)
        try:
            collection_check_status = self.isCollectionPresent(collection_name=collection_name, db_name=db_name)
            if collection_check_status:
                collection = self.getCollection(collection_name=collection_name, db_name=db_name)
                findAllRecords = collection.find()
                return findAllRecords
        except Exception as e:
            # project_logs(f"At findAllRecords: {e}",user_id=self.user_id,project_id=self.project_id,exception=True)
            raise Exception(f"(findAllRecords): Failed to find record for the given collection and database\n" + str(e))

    def findRecordOnQuery(self, db_name, collection_name, query):
        """
        """
        # project_logs("finding record on query",user_id=self.user_id,project_id=self.project_id)
        try:
            collection_check_status = self.isCollectionPresent(collection_name=collection_name, db_name=db_name)
            if collection_check_status:
                collection = self.getCollection(collection_name=collection_name, db_name=db_name)
                findRecords = collection.find(query)
                return findRecords
        except Exception as e:
            # project_logs(f"At findRecordQuery: {e}",user_id=self.user_id,project_id=self.project_id,exception=True)
            raise Exception(
                f"(findRecordOnQuery): Failed to find record for given query,collection or database\n" + str(e))

    def updateOneRecord(self, db_name, collection_name, query,prev):
        """
        """
        # project_logs("Updating one record",user_id=self.user_id,project_id=self.project_id)
        try:
            collection_check_status = self.isCollectionPresent(collection_name=collection_name, db_name=db_name)
            if collection_check_status:
                collection = self.getCollection(collection_name=collection_name, db_name=db_name)
                previous_records = self.findfirstRecord(db_name=db_name, collection_name=collection_name,query=prev)
                # new_records = query
                updated_record = collection.update_one(previous_records, query)
 
                return updated_record
        except Exception as e:
            # project_logs(f"At updateOneRecord: {e}",user_id=self.user_id,project_id=self.project_id,exception=True)
            raise Exception(
                f"(updateRecord): Failed to update the records with given collection query or database name.\n" + str(
                    e))

    def updateMultipleRecord(self, db_name, collection_name, query):
        """
        """
        # project_logs("Updating multiple records",user_id=self.user_id,project_id=self.project_id)
        try:
            collection_check_status = self.isCollectionPresent(collection_name=collection_name, db_name=db_name)
            if collection_check_status:
                collection = self.getCollection(collection_name=collection_name, db_name=db_name)
                previous_records = self.findAllRecords(db_name=db_name, collection_name=collection_name)
                new_records = query
                updated_records = collection.update_many(previous_records, new_records)
                return updated_records
        except Exception as e:
            # project_logs(f"At updateMultpleRecords: {e}",user_id=self.user_id,project_id=self.project_id,exception=True)
            raise Exception(
                f"(updateMultipleRecord): Failed to update the records with given collection query or database name.\n" + str(
                    e))

    def deleteRecord(self, db_name, collection_name, query):
        """
        """
        # project_logs("deleting Record",user_id=self.user_id,project_id=self.project_id)
        try:
            collection_check_status = self.isCollectionPresent(collection_name=collection_name, db_name=db_name)
            if collection_check_status:
                collection = self.getCollection(collection_name=collection_name, db_name=db_name)
                collection.delete_one(query)
                return "1 row deleted"
        except Exception as e:
            # project_logs(f"At deleteRecord: {e}",user_id=self.user_id,project_id=self.project_id,exception=True)
            raise Exception(
                f"(deleteRecord): Failed to update the records with given collection query or database name.\n" + str(
                    e))

    def deleteRecords(self, db_name, collection_name, query):
        """
        """
        # project_logs("Deleting Records",user_id=self.user_id,project_id=self.project_id)
        try:
            collection_check_status = self.isCollectionPresent(collection_name=collection_name, db_name=db_name)
            if collection_check_status:
                collection = self.getCollection(collection_name=collection_name, db_name=db_name)
                collection.delete_many(query)
                return "Multiple rows deleted"
        except Exception as e:
            # project_logs(f"At deleteRecords: {e}",user_id=self.user_id,project_id=self.project_id,exception=True)
            raise Exception(
                f"(deleteRecords): Failed to update the records with given collection query or database name.\n" + str(
                    e))

    def getDFCollection(self, db_name, collection_name):
        # project_logs("getting df from collection",user_id=self.user_id,project_id=self.project_id)
        try:
            all_Records = self.findAllRecords(collection_name=collection_name, db_name=db_name)
            dataframe = pd.DataFrame(all_Records)
            return dataframe
        except Exception as e:
            # project_logs(f"At DFToCollection: {e}",user_id=self.user_id,project_id=self.project_id,exception=True)
            raise Exception(
                f"(getDFCollection): Failed to get DatFrame from provided collection and database.\n" + str(e))

    def DFToCollection(self, collection_name, db_name, dataframe):
        # project_logs("Converting DF to Collection",user_id=self.user_id,project_id=self.project_id)
        try:
            collection_check_status = self.isCollectionPresent(collection_name=collection_name, db_name=db_name)
            dataframe_dict = json.loads(dataframe.T.to_json())
            if collection_check_status:
                self.insertRecords(collection_name=collection_name, db_name=db_name, records=dataframe_dict)
                return "Inserted"
            else:
                self.createDatabase(db_name=db_name)
                self.createCollection(collection_name=collection_name, db_name=db_name)
                self.insertRecords(db_name=db_name, collection_name=collection_name, records=dataframe_dict)
                return "Inserted"
        except Exception as e:
            # project_logs(f"At DFToCollection: {e}",user_id=self.user_id,project_id=self.project_id,exception=True)
            raise Exception(
                f"(DFToCollection): Failed to save dataframe value into collection.\n" + str(e))

    def getResults(self, db_name, collection_name):
        """
        This function returns the final result to display on browser.
        """
        # project_logs("getting results",user_id=self.user_id,project_id=self.project_id)
        try:
            response = self.findAllRecords(db_name=db_name, collection_name=collection_name)
            result = [i for i in response]
            return result
        except Exception as e:
            # project_logs(f"At getResult: {e}",user_id=self.user_id,project_id=self.project_id,exception=True)
            raise Exception(
                f"(getResults) - Something went wrong on getting result from database.\n" + str(e))
