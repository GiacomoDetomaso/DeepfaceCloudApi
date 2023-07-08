from deepface.commons.distance import findThreshold, findEuclideanDistance
from numpy import argmin
from rules.blobs import ObjectPersistenceManager
from os import remove
from os.path import isfile, join

import pickle
import time

# If this constant is set, the input parameter is skipped. It is primarily used
# on the username and info input parameter in the FaceRepresentation class. That's 
# because if the action of 'find the closest representation' is performed, the
# FaceRepresentationManager just needs the embeddings of the input image to find
# the closest FaceRepresentation object.
SKIP = 'skip'

# A constant that defines the name of the file that contains all the usernames
USERNAMES_BLOB = 'usernames.pkl'

# A constant that defines the name of the file that contains all the representations
REPRESENTATIONS_BLOB = 'representations.pkl'

class FaceRepresentation:

    def __init__(self, username=SKIP, info=SKIP, embedding=SKIP) -> None:
        """
            - username: the identity of the representation
            - info:     additional information
            If no value is specified for username and info, then the instance will
            be considered as an unknown FaceRepresentation. By default, the embedding
            is setted to None, if not generated by generate_representation_single_face method
        """
        self.username = username
        self.info = info
        self.embedding = embedding


class FaceOperation:
    def __init__(self, persistence_manager: ObjectPersistenceManager) -> None:
        self.persistence_manager = persistence_manager
        self.temp_download_folder = 'temp'


    @staticmethod
    def _clean_temp_file(folder):
        """
            Class method used to clean temporary files
        """
        path = join(folder, USERNAMES_BLOB)

        if isfile(path):
            remove(path)

        path = join(folder, REPRESENTATIONS_BLOB)

        if isfile(path):
            remove(path)
        

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
        usernames_path = join(self.temp_download_folder, USERNAMES_BLOB)
        representations_path = join(self.temp_download_folder, REPRESENTATIONS_BLOB)

        ret = False

        is_downloadable = self.persistence_manager.download(USERNAMES_BLOB, self.temp_download_folder)
        ret = is_downloadable

        if is_downloadable:
            is_downloadable = self.persistence_manager.download(REPRESENTATIONS_BLOB, self.temp_download_folder)
            ret = is_downloadable
            
            if is_downloadable:
                with open(usernames_path, 'rb') as f1, open(representations_path, 'rb') as f2:
                    usernames: set = pickle.loads(f1.read())
                    print(usernames)
                    representations: list = pickle.loads(f2.read())
                    
                    # If the identity is not present into the storage a ValueError is raised
                    if self.identity_to_delete not in usernames:
                        raise ValueError

                    rep_to_remove = next(rep for rep in representations if rep.username == self.identity_to_delete)

                    # Remove the identity and the representation
                    usernames.remove(self.identity_to_delete)
                    representations.remove(rep_to_remove)

                    print(len(representations))
            
                with open(usernames_path, 'wb') as f1, open(representations_path, 'wb') as f2:
                    f1.write(pickle.dumps(usernames))
                    f2.write(pickle.dumps(representations))

                with open(usernames_path, 'rb') as f1:
                    print(pickle.loads(f1.read()))

                self.persistence_manager.upload(usernames_path)
                self.persistence_manager.upload(representations_path)
      
                ret = True 
            
        self._clean_temp_file(self.temp_download_folder)
        
        return ret
    

class FaceRepresentationUploader(FaceOperation):
    def __init__(self, persistence_manager: ObjectPersistenceManager, rep: FaceRepresentation) -> None:
        """
            - persistence_manager: the specific storage manager, used to upload the FaceRepresentation
            - rep: the representation to upload
        """
        super(FaceRepresentationUploader, self).__init__(persistence_manager)
        self.rep = rep

        if rep.username is SKIP or rep.info is SKIP or rep.embedding is SKIP:
            raise ValueError('Could not perform this action. Username and info are setted as SKIP, or embedding is '
                             'not evaluated')
        

    def upload_representation(self) -> bool:
        """
            This method is used to upload the FaceRepresentation
            to the Blob storage on Azure.
                - Return:   a boolean value
        """
        # Register the username if it is not duplicated
        is_username_free = self.__register_username(self.rep.username)

        if is_username_free:
            # Read the pkl representation file
            is_downloadable = self.persistence_manager.download(REPRESENTATIONS_BLOB, self.temp_download_folder)

            local_representation_path = join(self.temp_download_folder, REPRESENTATIONS_BLOB)

            # If the data can be downloaded, open the file and extract 
            # the FaceRepresentations using pickle
            if is_downloadable:
                with open(local_representation_path, 'rb') as f:
                    representations: list = pickle.loads(f.read())
            else:
                # Instantiate an empty list if the file is not created
                representations: list = list()

            # Append the new representation    
            representations.append(self.rep)

            # Update the pickle file
            with open(local_representation_path, 'wb') as f:
                f.write(pickle.dumps(representations))

            self.persistence_manager.upload(local_representation_path)

        self._clean_temp_file(self.temp_download_folder)

        return is_username_free
    

    def __register_username(self, username) -> bool:
        """
            - username: the username to check
            - Return: This method returns True if the username is
            already registered, False otherwise
        """
        is_downloaded = self.persistence_manager.download(USERNAMES_BLOB, self.temp_download_folder)
        usernames_set = set()

        local_usernames_path = join(self.temp_download_folder, USERNAMES_BLOB)

        if is_downloaded:
            with open(local_usernames_path, 'rb') as f:
                usernames_set: set = pickle.loads(f.read())

        flag = username not in usernames_set

        if flag:
            usernames_set.add(username)

            with open(local_usernames_path, 'wb') as f:
                f.write(pickle.dumps(usernames_set))

            self.persistence_manager.upload(local_usernames_path)

        return flag


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
        is_downloaded = self.persistence_manager.download(REPRESENTATIONS_BLOB, self.temp_download_folder)
        tac = time.time()

        download_path = join(self.temp_download_folder, REPRESENTATIONS_BLOB)
        
        if is_downloaded:
            print(f'Downloaded representations data in {str(tac - tic)} seconds')
            with open(download_path, 'rb') as f:
                known_representations = pickle.loads(f.read())

            treshold = findThreshold(model_name=model, distance_metric=metric)

            # List that saves the distances scores of the i_th representation
            # against all the ones, already stored in the storage. It must be
            found_distances = list()

            for i, unknown in enumerate(self.source_representations):
                # For every unknown input representation, calculate the distances
                # againt all the known representations
                for j, known in enumerate(known_representations):
                    distance = findEuclideanDistance(known.embedding, unknown.embedding)
                    found_distances.append(distance)
                    print(f'{i} => {j}: {known.username} - distance: {distance}')

                # Find the index of the lowest distance
                if len(found_distances) == 1:
                    min_dist_index = 0
                else:
                    min_dist_index = argmin(found_distances)
                    print(min_dist_index)

                if len(found_distances) > 0 and found_distances[min_dist_index] <= treshold:
                    # Get the index of the minimum distance found during the process and extract the representation
                    entry: FaceRepresentation = known_representations[min_dist_index]
                    found_identities.append(f'{entry.username} - {entry.info}')
                    print(f'Generated identity for {i} - {min_dist_index} with min distance {found_distances[min_dist_index]}')
                
                # Clear the list at the end of cycle to save 
                # the distances for the next input representation
                found_distances.clear()

        self._clean_temp_file(self.temp_download_folder)
        
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

        if self.persistence_manager.download(REPRESENTATIONS_BLOB, self.temp_download_folder):
            download_path = join(self.temp_download_folder, REPRESENTATIONS_BLOB)
            
            # Get the target representation                
            with open(download_path, 'rb') as f:
                all_representation: list = pickle.loads(f.read())

            # Get if it exsists the unique representation with the target username
            target: FaceRepresentation = next(rep for rep in all_representation if rep.username == target_username)

            treshold = findThreshold(model, metric)
                
            found_distances: list = []

            for source in self.source_representations:
                found_distances.append(findEuclideanDistance(source.embedding, target.embedding))

            # If the min distance is less than the treshold value then the input 
            # representation contains the target identity
            contains = min(found_distances) <= treshold

        self._clean_temp_file(self.temp_download_folder)

        return contains   
