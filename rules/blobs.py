from azure.identity import ManagedIdentityCredential
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import ResourceNotFoundError
from os.path import isfile

from abc import ABC, abstractmethod

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
    def upload(self, file_name):
        """
            Upload a local file to the persistence storage. The name of the entity
            will be the same of the local file specified as input.
            - file_name:    the name of the local file, to upload
            - raise:        OSError if the file does not exists, or a generic
                            ValueError if the file could not be uploaded for generic issues
        """
        pass

    def download(self, target_file):
        """
            This method is used to download a blob, specifing its name.
            If the blob is downloaded, a local file with the downloaded
            content will be created
            - target_file:  the name of the target file to download. If it is successfuly downloaded
                            this will be the name of the local file too
            - raise:        ResourceNotFoundError if the specified blob doe not exists
        """
        pass
        

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
        
        self.persistence_location = container_name
        self.connection_string = connection_string
        self.container_client = self.__blob_service_setup()

    def __blob_service_setup(self):
        # Use a token to access Azure resources instead
        # This token is obtained via a Managed identity
        token_credential = ManagedIdentityCredential()

        if self.connection_string == 'skip':
            # Create the blob service client using the token
            blob_service_client = BlobServiceClient(
                account_url="https://deepfacestorage.blob.core.windows.net",
                credential=token_credential)
        else:
            blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)

        return blob_service_client.get_container_client(self.persistence_location)

    def upload(self, file_name: str):
        if not isfile(file_name):
            raise OSError('The input file path does not exists')

        with open(file_name, 'rb') as data:
            blob = self.container_client.upload_blob(file_name, data, overwrite=True)

        if blob is None:
            raise ValueError('The upload of the blob failed')

    def download(self, target_file: str) -> bool:
        can_download = True  # Specify if the resource is downloadable

        # Extract the stream data from the blob, handliing the exception if
        # the resource is not found
        try:
            downloaded_blob = self.container_client.download_blob(target_file)
        except ResourceNotFoundError:
            can_download = False

        # If the resource is downloadable write the bytes
        if can_download:
            with open(target_file, 'wb') as data:
                data.write(downloaded_blob.readall())

        return can_download


class LocalFileManager(ObjectPersistenceManager):
    pass