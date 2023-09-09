from abc import ABC, abstractmethod
from os.path import isfile, join

import pickle
import os

class ObjectPersistenceManager(ABC):
    """
        This class provides an interface to  upload or download
        object's files (such as pickle files) to a generic persistence's service. 
    """

    def __init__(self, persistence_location: str) -> None:
        """
            - persistence_location: the name of the location where the object will be saved
        """
        self.persistence_location = persistence_location

    @abstractmethod
    def upload(self, entity_name: str, data: any):
        """
            Upload a data to the persistence storage.
            - entity_name:  the name of the entity to upload
            - data:         the data to upload
            - raise:        OSError if the file does not exists, or a generic
                            ValueError if the file could not be uploaded for generic issues
        """
        pass

    @abstractmethod
    def download(self, entity_name: str) -> object:
        """
            This method is used to download an object stored in the 
            specific persistence location and identified by its entity name
            - entity_name:  the name of the entity to download
            - raise:        ResourceNotFoundError if the specified blob doe not exists
        """
        pass
    
    @abstractmethod
    def remove(self):
        """
            This methods removes the specified location from the storage.
        """

# Import dependencies for the Azure specialization of the ObjectPersistenceManager
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import ResourceNotFoundError

class AzureBlobManager(ObjectPersistenceManager):
    """
        This class inherits all of its services from the base ObjectPersistenceManager. 
        AzureBlobManager is specialized in uploading or downloading blobs 
        to or from the Azure Storage service.
    """

    def __init__(self, container_name: str, connection_string: str = 'skip'):
        """
            - container_name:       the name of the container to point. If the container does not
                                    exist, it's created by azure
            - connection_string:    if specified, perform the connection using this string.
        """
        super(AzureBlobManager, self).__init__(container_name)
        self.connection_string = connection_string
        self.container_client = self.__blob_service_setup()

    def __blob_service_setup(self):
        # Use a token to access Azure resources instead
        # This token is obtained via a Managed identity
        token_credential = DefaultAzureCredential()

        if self.connection_string == 'skip':
            # Create the blob service client using the token
            blob_service_client = BlobServiceClient(
                account_url="https://deepfacestorage.blob.core.windows.net",
                credential=token_credential)
        else:
            blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)

        return blob_service_client.get_container_client(self.persistence_location)

    def upload(self, blob_name: str, data: any):
        """
            Upload data to the persistence storage: Azure blob manager.
            - blob_name:    the name of the blob to upload
            - data:         the data to upload
            - raise:        ValueError if the file could not be uploaded for generic issues
        """
        # Write a temporary local file that will be uploaded to the blob storage
        path: str = join('temp', blob_name)
        with open(path, 'wb') as f: f.write(pickle.dumps(data))

        # Upload the temporary file to the blob storage
        with open(path, 'rb') as blob_data:
            blob = self.container_client.upload_blob(blob_name, blob_data, overwrite=True)

        if isfile(path) : os.remove(path)
            
        if blob is None:
            raise ValueError('The upload of the blob failed')
        
    def download(self, blob_name: str) -> object:
        """
            This method is used to download a blob stored in the 
            Azure blob manager and identified by its blob_name
            - entity_name:  the name of the entity to download
            - raise:        ResourceNotFoundError if the specified blob doe not exists
        """

        # Extract the stream data from the blob, handliing the exception if
        # the resource is not found
        try:
            downloaded_blob = self.container_client.download_blob(blob_name)
        except ResourceNotFoundError:
            downloaded_blob = None

        # If the resource is downloadable write the bytes
        if downloaded_blob is not None:
            downloaded_blob = pickle.loads(downloaded_blob.readall())

        return downloaded_blob
    
    def remove(self):
        self.container_client.delete_container()


# Import dependencies for the file sysem specialization of the ObjectPersistenceManager
from shutil import copyfile
from os import mkdir

class LocalFileManager(ObjectPersistenceManager):
    """
        This class inherits all of its services from the base ObjectPersistenceManager. 
        LocalFileManager is specialized in uploading or downloading data on the 
        local file system.
    """

    def __init__(self, persistence_location: str) -> None:
        super(LocalFileManager, self).__init__(persistence_location)
        self.folder = persistence_location

    def upload(self, file_name: str, data: any):
        """
            Upload data to the local file system.
            - file_name:    the name of the local file to upload
            - data:         the data to upload
            - raise:        OSError if the file does not exists, or a generic
                            ValueError if the file could not be uploaded for generic issues
        """
        # Create the folder to store data if it not exsist
        try:
            mkdir(self.folder)
        except FileExistsError:
            pass
        
        # Write a temporary local file that will be uploaded to the blob storage
        path: str = join(self.folder, file_name)
        with open(path, 'wb') as f: f.write(pickle.dumps(data))


    def download(self, file_name: str) -> object:
        """
            This method is used to download an object stored in the 
            local file system and identified by its entity name
            - entity_name:  the name of the entity to download
            - raise:        FileNotFoundError if the specified blob doe not exists
        """
        try:
            with open(join(self.persistence_location, file_name), 'rb') as f:
                    obj = pickle.loads(f.read())
        except FileNotFoundError:
            obj = None

        return obj
    
    def remove(self):
        return super().remove()
    

# Gobal dependencies for all Firebase products
from firebase_admin import initialize_app 

# Import dependencies for the Firestore specialization of the ObjectPersistenceManager
from firebase_admin import firestore
from google.cloud.firestore_v1.client import Client

class FirestoreDatabaseManager(ObjectPersistenceManager):
    """
        This class inherits all of its services from the base ObjectPersistenceManager. 
        FirebaseRealTimeDatabaseManager is specialized in uploading or downloading
        data to the real-time database of firebase.
    """

    def __init__(self, persistence_location: str, db_url: str) -> None:
        super(FirestoreDatabaseManager, self).__init__(persistence_location)
        self.db_url = db_url
        self.__firebase_fs_setup()

    def __firebase_fs_setup(self):
        """
            This method is used to initialize Firestore
        """
        initialize_app()
        self.db: Client = firestore.client()


# Import dependencies for the FirebaseStorage specialization of the ObjectPersistenceManager
from firebase_admin import storage

class FirebaseStorageManager(ObjectPersistenceManager):
    def __init__(self, persistence_location: str) -> None:
        super(FirebaseStorageManager, self).__init__(persistence_location)
        self.__firebase_storage_setup()

    def __firebase_storage_setup(self):
        """
            This method is used to initialize Firestore
        """
        initialize_app()
        self.storage: Client = firestore.client()

    def upload(self, file_path: str):
        return super().upload(file_path)    