from deepface.DeepFace import represent
from azure.core.exceptions import ResourceNotFoundError
import pickle
from modules.blobs import BlobManager

# A costant that defines the container of the blobs
CONTAINER_NAME = 'dfdb' 
# A costant that defines the name of the blob that contains all the usernames
USERNAMES_BLOB = 'usernames.pkl' 
# A costant that defines the name of the blob that contains all the representations
REPRESENTATIONS_BLOB = 'representations.pkl' 

class FaceRepresentation:

    def __init__(self, username, info) -> None:
        self.username = username
        self.info = info
        self.representation = None

    def generate_representation_single_face(self, img, backend, model) -> bool:
        '''
            TODO: WRITE DOC
        '''
        ret = True
        
        try:
            representation: dict = represent(img_path=img, detector_backend=backend, model_name=model)
            # The image must contains a single face
            if len(representation) == 1:
                embedding = representation[0]['embedding'] # extracts the face embedding
                facial_area = representation[0]['facial_area'] # extract face box coordinates
                
                # Set the embedding 
                self.representation = embedding

                # Set face points
                self.x1 = facial_area['x']
                self.y1 = facial_area['y']
                self.x2 = facial_area['x'] + facial_area['w']
                self.y2 = facial_area['y'] + facial_area['h']
            else: 
                ret = False
        except ValueError:
            ret = False

        return ret
    
class FaceRepresentationManager:
    
    __usernames_set = None

    def __init__(self, face_rep: FaceRepresentation) -> None:
        # Get an instance of the blob manager
        self.blob_manager = BlobManager(CONTAINER_NAME) 

        # Raise an error if the username already exsists
        if self.__check_username_registration(face_rep.username):
            raise ValueError('The username has already been registered. Cannot use this Face representation')
        
        # Raise an error if a FaceRepresentation without the face represented is passed
        if face_rep.representation is None:
            raise ValueError("You must load the face representation before passing this object to the manager")

        self.face_rep = face_rep

    def __check_username_registration(self, username) -> bool:
        '''
            - username: the username to check
            - Return: This method returns True if the username is 
            already registered, False otherwise
        '''
        is_downloadable = self.blob_manager.download_blob_to_file(USERNAMES_BLOB)

        if is_downloadable:
            with open(USERNAMES_BLOB, 'rb') as f:
                self.__usernames_set: set = pickle.loads(f.read())
            
            return username in self.__usernames_set
        else:
            # The username file is not present. An empty set can be instantiated
            self.__usernames_set = set()

    def upload_representation(self):
        '''
            This method is used to upload the FaceRepresentation
            to the Blob storage on Azure
        '''
        # Upload the updated usernames set
        self.__usernames_set.add(self.face_rep.username)

        # Update the pickle file
        with open(USERNAMES_BLOB, 'wb') as f:
            f.write(pickle.dumps(self.__usernames_set))

        self.blob_manager.upload_blob(USERNAMES_BLOB)

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
        representations.append(self.face_rep)

        # Update the pickle file
        with open(REPRESENTATIONS_BLOB, 'wb') as f:
            f.write(pickle.dumps(representations))

        self.blob_manager.upload_blob(REPRESENTATIONS_BLOB)

    def find_representation(self, img):
        '''
            TODO: redefine Serengill method to find the representation
        '''
        pass