# Import dependencies for the Azure specialization of the ObjectPersistenceManager
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import ResourceNotFoundError
from .opm import ObjectPersistenceManager
from os.path import join, isfile

import os
import pickle

class AzureBlobManager(ObjectPersistenceManager):
    """
        This class inherits all of its services from the base ObjectPersistenceManager. 
        AzureBlobManager is specialized in uploading or downloading blobs 
        to or from the Azure Storage service.
    """

    def __init__(self, container_name: str, connection_string: str = 'skip'):
        """
            Parameters
            ----------
            container_name: str       
                The name of the container where blobs will be uploaded.

            connection_string: str    
                If specified, perform the connection using this string.
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

    def upload(self, blob_name: str, data: object):
        """
            Uploads some object data to the Azure storage, specifing the name
            of the blob that will hold it. 

            Parameters
            ----------
            blob_name: str   
                The name of the blob to upload, that will contain the input data.

            data: object         
                The data object to upload as a blob. It must be serializable in 
                order to be uploaded.

            Raises
            ------
            ValueError 
                If the file could not be uploaded for generic issues.
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
            Azure blob manager and identified by its blob_name.

            Parameters
            ----------
            blob_name: str    
                The name of the blob to download from the Azure storage service.
            
            Return
            ------
            downloaded_blob: object
                The downloaded object.
            
            Raises
            ------
            ResourceNotFoundError 
                If the specified blob doe not exists.
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