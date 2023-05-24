from modules.operations import FaceRepresentation, FaceRepresentationManager, DeepFaceWrapper
from base64 import b64encode
from cv2 import imread, imwrite, rectangle

# Defines the detector backend and face recognition model used in the api
BACKEND = 'mtcnn'
MODEL = 'Facenet512'

# Defines the common keys of reply messages
KEY_MESSAGE = 'message'
KEY_STATUS = 'status'
KEY_FOUNDED_IDS = 'founded_ids'
KEY_COORDINATES = 'coordinates'
KEY_IMG_B64 = 'img_b64'

# Defines common values of status key
STATUS_FAIL = 'fail'
STATUS_SUCCESS = 'success'

# Defines default messages
NO_JSON_MESSAGE = 'You must send a json request, or request you have sent is empty'
EMPTY_MESSAGE = 'Empty input set passed'
ALL_VALUES_NOT_PASSED_MESSAGE = 'You must pass all values in order to perform this action'
BASE64_ERROR_MESSAGE = 'Input image is not base64 encoded'

# Defines json input param names
JSON_IMG = 'img'
JSON_USERNAME = 'username'
JSON_IDENTITY = 'identity'
JSON_INFO = 'info'

# Path to temporary file
TEMP_IMG = 'img.jpg'

# The manager to execute all the operations regarding a FaceRepresentation
_manager = FaceRepresentationManager()


def upload_representation(file_name: str, username: str, info: str) -> dict:
    """
        This method is used to upload a FaceRepresentation to Azure blob services.
            - file_name:    the name of the file where the image is stored
            - username:     the username associated to the face image
            - info:         addirional info on the FaceRepresentation
    """
    # Manage the exceptions that could occur
    try:
        wrapper = DeepFaceWrapper(file_name, BACKEND, MODEL)
        embeddings = wrapper.generate_embeddings()

        if len(embeddings) > 1:
            message = {KEY_MESSAGE: 'Could not create a representation: multiple faces detected', 
                       KEY_STATUS: STATUS_FAIL}
        else:
            face_representation = FaceRepresentation(username, info, embeddings[0])

            # Upload the representation to the storage and check the result to
            # return the correct response message to the client
            if _manager.upload_representation(face_representation):
                message = {KEY_MESSAGE: 'Representation generated',
                           KEY_STATUS: STATUS_SUCCESS}
            else:
                message = {KEY_MESSAGE: 'Representation not generated: duplicated username',
                           KEY_STATUS: STATUS_FAIL}

    except ValueError:
        message = {KEY_MESSAGE: 'Could not create a representation: no faces detected',
                   KEY_STATUS: STATUS_FAIL}

    return message


def find_representations(file_name: str) -> dict:
    """
        This method is used to find all the FaceRepresentation in a given image
            - file_name:    the name of the file where the image is stored
            - return:       a dictionary with the found identities
    """
    try:
        unknown_face_representations = list()

        wrapper = DeepFaceWrapper(file_name, BACKEND, MODEL)
        embeddings = wrapper.generate_embeddings()

        print(f'Generated: {len(embeddings)} embeddings')

        # Populate the unknown FaceRepresentation list with the embedding generated
        for embedding in embeddings:
            unknown_face_representations.append(FaceRepresentation(embedding=embedding))

        ids = _manager.find_closest_representations(unknown_face_representations, model=MODEL)

        # If the closest representation is correctly found determines the correct
        # repsonse message to send to the client
        if len(ids) == 0:
            message = {KEY_MESSAGE: 'Cannot find any close representation',
                       KEY_STATUS: STATUS_FAIL}
        else:
            message = {KEY_MESSAGE: 'Representation found',
                       KEY_STATUS: STATUS_SUCCESS, 
                       KEY_FOUNDED_IDS: ids}

    except ValueError:
        message = {KEY_MESSAGE: 'Could not create a representation: no faces detected',
                   KEY_STATUS: STATUS_FAIL}
    except OSError:
        message = {KEY_MESSAGE: 'Could not create a representation: internal errors',
                   KEY_STATUS: STATUS_FAIL}

    return message


def verify_representation(file_name: str, username: str) -> dict:
    """
        This method performs a face verification task. It verifies the
        presence of a certain person (identified by its username) in the
        input image.
            - file_name:    the name of the file where the image is stored
            - username:     the username to check in the image
            - returns:      a dictionary with a result message
    """
    wrapper = DeepFaceWrapper(file_name, BACKEND, MODEL)
    embeddings = wrapper.generate_embeddings()
    rep_list: list = list()

    print(f'{len(embeddings)} embeddings found in this image')
    
    for embedding in embeddings:
        rep_list.append(FaceRepresentation(embedding=embedding))

    try:
        val = _manager.verify_identity(rep_list, username)
        message = {KEY_MESSAGE: str(val), 
                   KEY_STATUS: STATUS_SUCCESS}
    except StopIteration: 
        # This exception is raised if the input username does not exsist 
        message = {KEY_MESSAGE: 'The identity provided does not exsists', 
                   KEY_STATUS: STATUS_FAIL}

    return message


def extract_faces(file_name: str, return_image=False):
    """
        This method is used to extract all the faces from the input image
            - file_name:    the name of the file where the image is stored
            - return_image: if False the method returns a list with the face coordinates, otherwise
                            the method returns a base64 encoded image with the facial areas drawn on it
            - return:       a list of face coordinates or a b64 encoded image, according to return_image param
            - raise:        a ValueError if the face is not found in the image
    """
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
