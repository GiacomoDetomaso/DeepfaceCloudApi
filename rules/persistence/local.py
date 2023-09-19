# Import dependencies for the file sysem specialization of the ObjectPersistenceManager
from os import mkdir
from os.path import join
from .opm import ObjectPersistenceManager

import pickle

class LocalFileManager(ObjectPersistenceManager):
    """
        This class inherits all of its services from the base ObjectPersistenceManager. 
        LocalFileManager is specialized in uploading or downloading data on the 
        local file system.
    """

    def __init__(self, persistence_location: str) -> None:
        super(LocalFileManager, self).__init__(persistence_location)
        self.folder = persistence_location

    def upload(self, file_name: str, data: object):
        """
            Uploads some object data to the local file system, specifing the name
            of the file that will hold it.

            Parameters
            ----------
            file_name:    
                The name of the local file to upload, that will contain the input data.

            data: object        
                The data object to upload as pickle file. It must be serializable in 
                order to be uploaded.

            Raises
            ------
            OSError 
                If the file does not exists.

            ValueError 
                If the file could not be uploaded for generic issues.
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
            local file system and identified by its file name.

            Parameters
            ----------
            file_name: str 
                The name of the file to download.
            
            Raises
            ------
            FileNotFoundError 
                If the specified blob doe not exists.
        """
        try:
            with open(join(self.persistence_location, file_name), 'rb') as f:
                    obj = pickle.loads(f.read())
        except FileNotFoundError:
            obj = None

        return obj
    
    def remove(self):
        return super().remove()