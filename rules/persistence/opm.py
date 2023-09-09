from abc import ABC, abstractmethod

class ObjectPersistenceManager(ABC):
    """
        This class provides an interface to  upload or download
        object's files to a generic persistence's service. 
    """

    def __init__(self, persistence_location: str) -> None:
        """
            Parameters
            ----------
            persistence_location: str 
                the name of the location where the object will be saved
        """
        self.persistence_location = persistence_location

    @abstractmethod
    def upload(self, entity_name: str, data: any):
        """
            Upload some data to the persistence storage, specifing the name
            of the entity that will hold them.

            Parameters
            ----------
            entity_name: str 
                The name associated to the data to upload.

            data: any         
                The actual data to upload.

            Raises
            ------
            OSError 
                If the file does not exists, or a generic.

            ValueError 
                If the file could not be uploaded for generic issues.
        """
        pass

    @abstractmethod
    def download(self, entity_name: str) -> object:
        """
            This method is used to download an object stored in the 
            specific persistence location and identified by its entity name.

            Parameters
            ----------
            entity_name: str  
                The name associated a the data to download.

            Return
            ------
            obj: object
                The object retrieved from the download.

            Raises
            ------
            ResourceNotFoundError 
                If the specified blob doe not exists
        """
        pass
    
    @abstractmethod
    def remove(self):
        """
            This methods removes the specified location from the storage.
        """