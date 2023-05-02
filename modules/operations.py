from deepface.DeepFace import represent
from deepface.commons.distance import findThreshold, findCosineDistance, findEuclideanDistance
from numpy import argmin
from modules.blobs import BlobManager
from os import remove
from os.path import isfile
import pickle

# If this costant is setted, the input parameter is skipped. It is primarly used
# on the username and info input parameter in the FaceRepresentation class. That's 
# because if the action of 'find the closest representetion' is performed, the 
# FaceRepresentationManager just needs the embeddings of the input image to find
# the closest FaceRepresentation object.
SKIP = 'skip'
# A costant that defines the container of the blobs
CONTAINER_NAME = 'dfdb' 
# A costant that defines the name of the blob that contains all the usernames
USERNAMES_BLOB = 'usernames.pkl' 
# A costant that defines the name of the blob that contains all the representations
REPRESENTATIONS_BLOB = 'representations.pkl' 
#CONNECTION_STRING = "DefaultEndpointsProtocol=https;AccountName=deepfacestorage;AccountKey=hhhh7CjfFqZTl6pK9UryXwy8fKMrdxiuAJQ9mttXhLpGSAaJzL/3KqHw7JJ7FEAboMlW5jNNm8UOQVWv+ASt7o/sNg==;EndpointSuffix=core.windows.net"
class FaceRepresentation:

    def __init__(self, username=SKIP, info=SKIP) -> None:
        self.username = username
        self.info = info
        self.embedding = None

    def generate_representation_single_face(self, img, backend, model) -> bool:
        '''
            TODO: WRITE DOC
        '''
        ret = True
        
        representation: dict = represent(img_path=img, detector_backend=backend, model_name=model)
        # The image must contains a single face
        if len(representation) == 1:
            embedding = representation[0]['embedding'] # extracts the face embedding
            facial_area = representation[0]['facial_area'] # extract face box coordinates
                
            # Set the embedding 
            self.embedding = embedding

            # Set face points
            self.x1 = facial_area['x']
            self.y1 = facial_area['y']
            self.x2 = facial_area['x'] + facial_area['w']
            self.y2 = facial_area['y'] + facial_area['h']
        else: 
            ret = False

        return ret
    
class FaceRepresentationManager:
    
    def __init__(self, rep) -> None:
        self.blob_manager = BlobManager(CONTAINER_NAME) # Get an instance of the blob manager
        self.rep = rep

    @classmethod
    def init_upload(cls, face_rep: FaceRepresentation):
        if not isinstance(face_rep, FaceRepresentation):
            raise ValueError('You must pass a FaceRepresentation object')
        
        # Raise an error if a FaceRepresentation without the face represented is passed
        if face_rep.embedding is None:
            raise ValueError("You must load the face representation before passing this object to the manager")
        
        return cls(face_rep)
    
    def __clean_temp_file(self):
        '''
            Class method used to clean temporary files
        '''
        if isfile(USERNAMES_BLOB):
            remove(USERNAMES_BLOB)

        if isfile(REPRESENTATIONS_BLOB):
            remove(REPRESENTATIONS_BLOB)

    def upload_representation(self) -> bool:
        '''
            This method is used to upload the FaceRepresentation
            to the Blob storage on Azure.
            - Return: a boolean value
        '''
        if self.rep.username is SKIP or self.rep.info is SKIP:
            raise ValueError('Could not perform this action. Username and info are setted as SKIP')

        # Register the username if it is not duplicated
        is_username_free = self.__register_username(self.rep.username)

        if is_username_free:
            # Read the pkl representation file
            is_downloadable = self.blob_manager.download_blob_to_file(REPRESENTATIONS_BLOB)

            # If the data can be downloaded, open the file and extract 
            # the FaceRepresentations using pickle
            if is_downloadable:
                with open(REPRESENTATIONS_BLOB, 'rb') as f:
                    representations: list = pickle.loads(f.read())
            else:
                # Instantiate an empty list if the file is not created
                representations: list = list()

            # Append the new representation    
            representations.append(self.rep)

            # Update the pickle file
            with open(REPRESENTATIONS_BLOB, 'wb') as f:
                f.write(pickle.dumps(representations))

            self.blob_manager.upload_blob(REPRESENTATIONS_BLOB)
        
        self.__clean_temp_file()
        
        return is_username_free
    
    def remove_representation_by_username(self, username):
        # not implemented yet
        pass

    def find_closest_representation(self, metric='cosine'):
        '''
            This method is used to find the FaceRepresentation 
            whose embeddings are the closest possible to the FaceRepresentation 
            setted as input of the class, during init operations
            - metric:   the metric used to evaluate the distance between the representations. 
                        [cosine, euclidean]
            - return:   the class input FaceRepresentation object with the username and info field 
                        evaluated with the ones of the closest FaceReresentation found in the storage. 
                        None otherwise.
        '''
        found_representation = None
        
        is_downloaded = self.blob_manager.download_blob_to_file(REPRESENTATIONS_BLOB)

        if is_downloaded:
            with open(REPRESENTATIONS_BLOB, 'rb') as f:
                all_face_representations = pickle.loads(f.read())

            treshold = findThreshold(model_name='Facenet', distance_metric=metric)
            found_distances = list()

            for representation in all_face_representations:
                distance = findCosineDistance(representation.embedding, self.rep.embedding)
                print(distance)
                found_distances.append(distance)

            if len(found_distances) == 1:
                min_dist_index = 0
            elif len(found_distances) > 1:
                print(argmin(found_distances))
                min_dist_index = argmin(found_distances)
            
            if found_distances[min_dist_index] <= treshold:
                # Get the index of the minimum distance found during the process and extract the representation
                found_representation: FaceRepresentation = all_face_representations[min_dist_index]
                
                # Evaluate the class input FaceRepresentation with the missing values and returns it
                self.rep.username = found_representation.username
                self.rep.info = found_representation.info

        self.__clean_temp_file()
        return found_representation

    def __register_username(self, username) -> bool:
        '''
            - username: the username to check
            - Return: This method returns True if the username is 
            already registered, False otherwise
        '''
        is_downloaded = self.blob_manager.download_blob_to_file(USERNAMES_BLOB)
        usernames_set = set()

        if is_downloaded:
            with open(USERNAMES_BLOB, 'rb') as f:
                usernames_set: set = pickle.loads(f.read())
        
        flag = username not in usernames_set

        if flag:
            usernames_set.add(username)

            with open(USERNAMES_BLOB, 'wb') as f:
                f.write(pickle.dumps(usernames_set))

            self.blob_manager.upload_blob(USERNAMES_BLOB)

        return flag
    
    def __is_representation_embedding_unique(self, all_rep: list):
        for rep in all_rep:
            if self.rep.embedding == rep.embedding:
                return False
            
        return True