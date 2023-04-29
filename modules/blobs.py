from azure.identity import ManagedIdentityCredential
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import ResourceNotFoundError

class BlobManager:

    def __init__(self, container_name: str, connection_string: str = 'skip'):
        self.container_name = container_name
        self.connection_string = connection_string
        self.container_client = self.__blob_service_setup()

    def __blob_service_setup(self):
        # Use a token to access Azure resources instead
        token_credential = ManagedIdentityCredential()
        
        if self.connection_string is 'skip':
            # Create the blob service client using the token
            blob_service_client = BlobServiceClient(
                account_url="https://deepfacestorage.blob.core.windows.net",
                credential=token_credential)
        else:
            blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)
            
        return blob_service_client.get_container_client(self.container_name)

    def upload_blob(self, file_name: str):
        with open(file_name, 'rb') as data:
            blob = self.container_client.upload_blob(file_name, data, overwrite=True)

        if (blob is None):
            raise ValueError('The upload of the blob failed')
        
    def download_blob_to_file(self, file_name: str) -> bool:
        '''
            This method is used to download a blob, specifing its name.
            If the blob is downloaded, a local file with the blob name ù
            and content will be created.
            - file_name: the name of the blob file. If the blob is successfuly downloaded 
            this will be the name of the local file too
            - Returns: a boolean value to specify the correctness of the operation
        '''
        can_download = True # Specify if the resource is downloadable

        # Extract the stream data from the blob, handliing the exception if
        # the resource is not found
        try:
            downloaded_blob = self.container_client.download_blob(file_name)
        except ResourceNotFoundError:
            can_download = False
        
        # If the resource is downloadable write the bytes
        if can_download:
            with open(file_name, 'wb') as data:
                data.write(downloaded_blob.readall())
        
        return can_download