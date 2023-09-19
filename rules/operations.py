from deepface.commons.distance import findThreshold, findEuclideanDistance
from numpy import argmin
from .persistence.opm import ObjectPersistenceManager
from os import remove
from os.path import isfile, join
from pandas import DataFrame

import time

# If this constant is set, the input parameter is skipped. It is primarily used
# on the username and info input parameter in the FaceRepresentation class. That's 
# because if the action of 'find the closest representation' is performed, the
# FaceRepresentationManager just needs the embeddings of the input image to find
# the closest FaceRepresentation object.
SKIP = 'skip'

# A constant that defines the name of the file that contains all the representations
REPRESENTATIONS_BLOB = 'representations.pkl'

class FaceOperation:
    def __init__(self, persistence_manager: ObjectPersistenceManager) -> None:
        self.persistence_manager = persistence_manager
        self.temp_download_folder = 'temp'

    @staticmethod
    def _clean_temp_file(folder):
        """
            Class method used to clean temporary files
        """
        path = join(folder, REPRESENTATIONS_BLOB)

        if isfile(path):
            remove(path)
    
    @classmethod
    def get_dataframe_from_representations(cls, reps: list):
        """
            This class method is used to cast a list of face representations
            in a pandas Dataframe that will be used to quickly check 
            the status of the storage while Face operation are running
        """
        return DataFrame(reps)
    
        

class FaceRepresentationDeleter(FaceOperation):
    def __init__(self, persistence_manager: ObjectPersistenceManager, identity_to_delete) -> None:
        """
            - persistence_manager:  the specific storage manager, used to upload the FaceRepresentation
            - identity_to_delete:   the identity to delete from the storage
        """
        super(FaceRepresentationDeleter, self).__init__(persistence_manager)
        self.identity_to_delete = identity_to_delete

    def delete_representation(self) -> bool:
        """
            This method is used to delete the specified face representation
            identitfied by the idenitity provided as class-input.
            - Return:   boolean value which represent the outcome of the operation
            - Raise:    ValueError if the identity is not present. OSError if the update of the storage is unsuccessful
        """
        ret = False

        representations: list  = self.persistence_manager.download(REPRESENTATIONS_BLOB)
   
        if representations is not None:
            df = self.get_dataframe_from_representations(representations)
                
            # If the identity is not present into the storage a ValueError is raised
            if self.identity_to_delete not in df['username'].values:                    
                raise ValueError
            
            rep_to_remove = next(rep for rep in representations if rep['username'] == self.identity_to_delete)
            # Remove the identity and the representation
            representations.remove(rep_to_remove)
            
            print(len(representations))

            self.persistence_manager.upload(REPRESENTATIONS_BLOB, representations)
            ret = True 
                    
        return ret
    

class FaceRepresentationUploader(FaceOperation):
    def __init__(self, persistence_manager: ObjectPersistenceManager, rep: dict) -> None:
        """
            - persistence_manager: the specific storage manager, used to upload the FaceRepresentation
            - rep: the representation to upload
        """
        super(FaceRepresentationUploader, self).__init__(persistence_manager)
        self.rep = rep

        if (rep.get('username', SKIP) is SKIP or 
            rep.get('info', SKIP) is SKIP or 
            rep.get('embedding', SKIP) is SKIP):
        
            raise ValueError('Could not perform this action. Username and info are setted as SKIP ',
                             'or embedding is not evaluated')
        

    def upload_representation(self) -> bool:
        """
            This method is used to upload the FaceRepresentation
            to the storage location.
                - Raise:    OSError if the file does not exists, or a generic
                            ValueError if the file could not be uploaded for generic issues
                - Return:   a boolean value to determine the status of the upload
        """
        representations: list = self.persistence_manager.download(REPRESENTATIONS_BLOB)

        # Instantiate an empty list if no representations were previously saved
        if representations is None:            
            representations: list = list()

        # Append the new representation    
        representations.append(self.rep)

        # Control flags
        duplicated_username = False
        upload_status = False

        # Check for duplicate usernames
        if len(representations) > 1:
            df = self.get_dataframe_from_representations(representations)
            
            print("Current Dataframe:")
            print(df)

            if True in df.duplicated(subset=['username']).values: 
                print(df.duplicated(subset=['username']))
                duplicated_username = True

        # Upload the updated representations if no duplicates are detected
        if not duplicated_username:
            self.persistence_manager.upload(REPRESENTATIONS_BLOB, representations)  
            upload_status = True 

        return upload_status

    
class FaceRecognizer(FaceOperation): 
    def __init__(self, persistence_manager: ObjectPersistenceManager, source_representations: list) -> None:
        """
            - persistence_manager: the specific storage manager, used to retrieve the stored representations
            - source_representations: a list of unknown representations
        """
        super(FaceRecognizer, self).__init__(persistence_manager)
        self.source_representations = source_representations


    def find_closest_representations(self, metric='euclidean', model='Facenet512') -> list:
        """
            This method is used to find the FaceRepresentation
            whose embeddings are the closest possible to the FaceRepresentation
            setted as input of the class during init operations
                - metric:   the metric used to evaluate the distance between the representations.
                            [cosine, euclidean]
                - return:   a list of the found identies from the input FaceRepresentation list
                - raise:    ValueError if no distances are found
        """
        found_identities = list()

        tic = time.time()
        known_representations: list = self.persistence_manager.download(REPRESENTATIONS_BLOB)
        tac = time.time()
        
        if known_representations is not None:
            print(f'Downloaded representations data in {str(tac - tic)} seconds')

            treshold = findThreshold(model_name=model, distance_metric=metric)

            # List that saves the distances scores of the i_th representation
            # against all the ones, already stored in the storage. It must be
            found_distances = list()

            for i, unknown in enumerate(self.source_representations):
                # For every unknown input representation, calculate the distances
                # againt all the known representations
                for j, known in enumerate(known_representations):
                    distance = findEuclideanDistance(known['embedding'], unknown['embedding'])
                    found_distances.append(distance)
                    print(f'{i} => {j}: {known["username"]} - distance: {distance}')

                # Find the index of the lowest distance
                if len(found_distances) == 1:
                    min_dist_index = 0
                else:
                    min_dist_index = argmin(found_distances)
                    print(min_dist_index)

                if len(found_distances) > 0 and found_distances[min_dist_index] <= treshold:
                    # Get the index of the minimum distance found during the process and extract the representation
                    entry: dict = known_representations[min_dist_index]
                    found_identities.append(f'{entry["username"]} - {entry["info"]}')
                    print(f'Generated identity for {i} - {min_dist_index} with min distance {found_distances[min_dist_index]}')
                
                # Clear the list at the end of cycle to save 
                # the distances for the next input representation
                found_distances.clear()
        
        return found_identities
    

    def verify_identity(self, target_username: str, model='Facenet512', metric='euclidean') -> bool:
        """
            This method is used to verify if the source representation corresponds
            to the target representation identified by the username. It's a verification-like task.
                - source: the source list of representations to be verified
                - target_username: the unique id of the representation which will be evaluated against source                    - return: a boolean value according to the operation status
                - raise: StopIteration if the target_username does not exist
            """
        contains = False

        all_representation: list = self.persistence_manager.download(REPRESENTATIONS_BLOB)

        if all_representation is not None:
            # Get if it exsists the unique representation with the target username
            target: dict = next(rep for rep in all_representation if rep['username'] == target_username)

            treshold = findThreshold(model, metric)
                
            found_distances: list = []

            for source in self.source_representations:
                found_distances.append(findEuclideanDistance(source['embedding'], target['embedding']))

            # If the min distance is less than the treshold value then the input 
            # representation contains the target identity
            contains = min(found_distances) <= treshold

        return contains   
