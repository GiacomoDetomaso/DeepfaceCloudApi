from modules.operations import FaceRepresentation, FaceRepresentationManager, DeepFaceWrapper
from base64 import b64encode
from cv2 import imread, imwrite, rectangle

# Defines the detector backend and face recognition model used in the api
BACKEND = 'mtcnn'
MODEL = 'Facenet512'

# The manager to execute all the operations regarding a FaceRepresentation
manager = FaceRepresentationManager()

def upload_representation(file_name: str, username: str, info: str) -> dict:
    '''
        This method is used to upload a FaceRepresentation to Azure blob services.
            - file_name:    the name of the file where the image is stored
            - username:     the username associated to the face image
            - info:         addirional info on the FaceReprentation    
    '''
     # Manage the exceptions that could occur
    try:
        wrapper = DeepFaceWrapper(file_name, BACKEND, MODEL)
        embeddings = wrapper.generate_embeddings()

        if len(embeddings) > 1:
            message = {'message': 'Could not create a representation: multiple faces detected'}
        else:
            face_representation = FaceRepresentation(username, info, embeddings[0])

            # Upload the representation to the stoage and ckech the result to 
            # return the correct response message to the client
            if manager.upload_representation(face_representation):
                message = {'message': 'Representation generated'}
            else:
                 message = {'message': 'Representation not generated: duplicated username'}

    except ValueError:
         message = {'message': 'Could not create a representation: no faces detected'}

    return message


def find_representations(file_name: str) -> dict:
    '''
        This method is used to find all the FaceRepresentation in a given image
            - file_name:    the name of the file where the image is stored 
            - return:       a dictionary with the found identities
    '''
    try:
        unknown_face_representations = list()

        wrapper = DeepFaceWrapper(file_name, BACKEND, MODEL)
        emebeddings = wrapper.generate_embeddings()

        print(f'Generated: {len(emebeddings)} embeddings')
            
        # Populate the unknown FaceRepresentation list with the embedding generated
        for embedding in emebeddings:
            unknown_face_representations.append(FaceRepresentation(embedding=embedding))

        ids = manager.find_closest_representations(unknown_face_representations, model=MODEL)

        # If the closest representation is correctly found determines the correct
        # repsonse message to send to the client
        if len(ids) == 0:
            message = {'message': 'Cannot find any close representation'}
        else:
            message = {'message': 'Success!', 'founded_ids': ids}
                
    except ValueError:
                message = {'message': 'Could not create a representation: no faces detected'}
    except OSError:
                message = {'message': 'Could not create a representation: internal errors'}

    return message


def verify_representation(file_name: str, username: str) -> dict:
    '''
        This method performs a face verification task. It verifies the 
        presence of a certain person (identified by its username) in the
        input image.
            - file_name:    the name of the file where the image is stored
            - username:     the username to check in the image
            - returns:      a dictionary with a result message
    '''
    wrapper = DeepFaceWrapper(file_name, BACKEND, MODEL)
    embeddings = wrapper.generate_embeddings()

    if len(embeddings) == 1:
        face_representation = FaceRepresentation(embedding=embeddings[0])

        try:
            val = manager.verify_identity(face_representation, username)
            message = {'message': str(val)}
        except StopIteration: # This exception is raised if the input username does not exsist
            message = {'message': 'The identity provided does not exsists'}
    else:
        message = {'message': 'Could not create a representation: multiple faces detected'}

    return message


def extract_faces(file_name: str, return_image=False):
    '''
        This method is used to extract all the faces from the input image
            - file_name:    the name of the file where the image is stored
            - return_image: if False the method returns a list with the face coordinates, otherwise
                            the method returns a base64 encoded image with the facial areas drawn on it
            - return:       a list of face coordinates or a b64 encoded image, according to return_image param
            - raise:        a ValueError if the face is not found in the image
    '''
    wrapper = DeepFaceWrapper(file_name, BACKEND, MODEL)
    areas = wrapper.extract_facial_areas() 

    if return_image:
        img = imread(filename=file_name)

        for area in areas:
            pt1 = (area['x1'], area['y1'])
            pt2 = (area['x2'], area['y2'])
            img = rectangle(img, pt1, pt2, (255, 255, 0), 1)

        # Write the modified img to a file
        imwrite(file_name, img) 

        # Turn the image into b64 
        with open(file_name, 'rb') as data:
             encoded_bytes = b64encode(data.read())
        
        img = encoded_bytes.decode('utf-8')

        return img
    else:
        return areas