from azure.identity import ManagedIdentityCredential
from azure.storage.blob import BlobServiceClient

class BlobManager:

    def __init__(self, container_name):
        # no values needed
        self.container_name = container_name
        self.container_client = self.__blob_service_setup()

    def __blob_service_setup(self):
        # Use a token to access Azure resources instead
        token_credential = ManagedIdentityCredential()

        # Create the blob service client using the token
        blob_service_client = BlobServiceClient(
            account_url="https://deepfacestorage.blob.core.windows.net",
            credential=token_credential)
        
        return blob_service_client.get_container_client(self.container_name)

    def upload_blob(self, file_name):
        with open(file_name, 'rb') as data:
            blob = self.container_client.upload_blob(file_name, data)

        if (blob is None):
            raise ValueError('The upload of the blob failed')
        
    def download_blob(self, file_name):
        # not implemented yet
        pass