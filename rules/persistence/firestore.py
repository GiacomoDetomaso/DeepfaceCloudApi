# Gobal dependencies for all Firebase products
from firebase_admin import initialize_app 
from typing import Union
from .opm import ObjectPersistenceManager

# Import dependencies for the Firestore specialization of the ObjectPersistenceManager
from firebase_admin import firestore
from google.cloud.firestore_v1.client import Client

class FirestoreDatabaseManager(ObjectPersistenceManager):
    """
        This class inherits all of its services from the base ObjectPersistenceManager. 
        FirestoreDatabaseManager is specialized in uploading or downloading
        data to the Firestore database service of firebase.
    """

    def __init__(self, persistence_location: str, db_url: str) -> None:
        super(FirestoreDatabaseManager, self).__init__(persistence_location)
        self.db_url = db_url
        self.__firebase_fs_setup()

    def __firebase_fs_setup(self):
        """
            This method is used to initialize Firestore.
        """
        initialize_app()
        self.db: Client = firestore.client()

    def upload(self, collection_name: str, data: Union[list[object], list[dict], dict,]):
        """
            Uploads some object data to the the Firestore database service of firebase, specifing the name
            of the collection that will hold it.

            Parameters
            ----------
            collection_name: str  
                The name of the collection to upload

            data: Union[list[object], list[dict], dict,]             
                The data object to upload. It must be: 1) a list of objects, where each of them 
                can be turned into a dict. 2) A list of dict. 3) A single dict.

            Raises
            ------
            OSError 
                If the file does not exists
            
            ValueError 
                If the file could not be uploaded for generic issues.
        """
        return super().upload(collection_name, data)
    
    def download(self, entity_name: str) -> object:
        return super().download(entity_name)
    
    def remove(self):
        return super().remove()