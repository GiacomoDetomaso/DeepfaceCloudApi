# Gobal dependencies for all Firebase products
from firebase_admin import initialize_app 
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

    def __init__(self, collection: str = "skip") -> None:
        super(FirestoreDatabaseManager, self).__init__(collection)
        self.__firebase_fs_setup()

    def __firebase_fs_setup(self):
        """
            This method is used to initialize Firestore.
        """
        initialize_app()
        self.db: Client = firestore.client()

    def upload(self, collection_name: str, data: list[dict]):
        """
            Uploads some object data to the the Firestore database service of firebase, specifing the name
            of the collection that will hold it.

            Parameters
            ----------
            collection_name: str  
                The name of the collection to upload

            data: Union[list[object], list[dict],]             
                The data object to upload. It must be: 1) a list of objects, where each of them 
                can be turned into a dict. 2) A list of dict. 3) A single dict.

            Raises
            ------
            OSError 
                If the file does not exists

            TypeError
                If data does not have __dict__ attribute
            
            ValueError 
                If the file could not be uploaded for generic issues.
        """
        self.persistence_location = collection_name

        # The first step is to check if the members of the list are dict or not
        if not all(isinstance(dt, dict) for dt in data):
            data = map(lambda d : vars(d), data)

        # Add the data to the collection
        for d in data:
            self.db.collection(collection_name).document(d['username']).set(d)

    def download(self, collection_name: str) -> list[dict]:
        """
            This method is used to download an entire collection from the firestore
            specificing its name.

            Parameters
            ----------
            collection_name: str  
                The name associated of the collection to download.

            Return
            ------
            obj: object
                A list of dictionary representing all documents under the collection.
        """
        docs = self.db.collection(collection_name).stream()
        obj = list()
        
        for doc in docs:
            obj.append(doc.to_dict())

        return obj
        
    
    def remove(self):
        return super().remove()
