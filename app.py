from flask import Flask, render_template, request, jsonify
from json import loads
from base64 import b64decode
from os import remove
from os.path import isfile
from modules.services import upload_representation, find_representations, verify_representation, extract_faces
from binascii import Error

app = Flask(__name__)

# Defines default messages
NO_JSON_MESSAGE = 'You must send a json request, or request you have sent is empty'
EMPTY_MESSAGE = 'Empty input set passed'
ALL_VALUES_NOT_PASSED_MESSAGE = 'You must pass all values in order to perform this action'
BASE64_ERROR_MESSAGE = 'Input image is not base64 encoded'

# Path to temporary file
TEMP_IMG = 'img.jpg'


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/detect/coordinates', methods=['POST'])
def detect_coordinates():
    """
        This method is used to detect the coordinates of a face into the input image
            - img:  the image in which the face will be detected
    """
    message = {'message': NO_JSON_MESSAGE}

    if request.is_json:
        input_arg: dict = loads(request.get_data())

        if input_arg is None:
            return jsonify({'message': EMPTY_MESSAGE})

        # Get the input value from the json string 
        img: str = input_arg.get('img')

        # Check the input correctness
        if img is None or not img:
            return jsonify({'message': 'img Field must be present and be not empty'})

        if _create_temporary_image_from_b64(img):
            try:
                coordinates = extract_faces(TEMP_IMG)
                message = {'message': 'Success!', 'Coordinates': coordinates}
            except ValueError:
                message = {'message': 'Could not detect any face in the given image'}

        if isfile(TEMP_IMG):
            remove(TEMP_IMG)  # clean temporary file

    return jsonify(message)


@app.route('/detect/faceboxes', methods=['POST'])
def detect_faceboxes():
    """
        This method is used to detect the coordinates of a face into the input image
            - img:  the image in which the face will be detected
    """
    message = {'message': NO_JSON_MESSAGE}

    if request.is_json:
        input_arg: dict = loads(request.get_data())

        if input_arg is None:
            return jsonify({'message': EMPTY_MESSAGE})

        # Get the input value from the json string 
        img: str = input_arg.get('img')

        # Check the input correctness
        if img is None or not img:
            return jsonify({'message': 'img Field must be present and be not empty'})

        if _create_temporary_image_from_b64(img):
            try:
                b64_img = extract_faces(TEMP_IMG, return_image=True)
                message = {'message': 'Success!', 'img_b64': b64_img}
            except ValueError:
                message = {'message': 'Could not detect any face in the given image'}

        if isfile(TEMP_IMG):
            remove(TEMP_IMG)  # clean temporary file

    return jsonify(message)


@app.route('/verify', methods=['POST'])
def verify():
    """
        This method verifies that the input image contains the person identified
        by a username.
            - img:      a base64 encoded image that must contains a single face to be verfied
            - identity: the stored id of the person searched in the img
    """
    message = {'message': NO_JSON_MESSAGE}

    if request.is_json:
        input_arg: dict = loads(request.get_data())

        if input_arg is None:
            return jsonify({'message': EMPTY_MESSAGE})

        # Get the input value from the json string 
        img: str = input_arg.get('img')
        identity: str = input_arg.get('identity')

        # Check the input correctness
        if img is None or identity is None:
            return jsonify({'message': ALL_VALUES_NOT_PASSED_MESSAGE})
        if not img or not identity:
            return jsonify({'message': 'Some of the input is empty'})

        if _create_temporary_image_from_b64(img):
            message = verify_representation(TEMP_IMG, identity)
        else:
            return jsonify({'message': BASE64_ERROR_MESSAGE})

        if isfile(TEMP_IMG):
            remove(TEMP_IMG)  # clean temporary file

    return jsonify(message)


@app.route('/represent', methods=['POST'])
def represent():
    """
        This method gives a representation of the face in the input image
        using Facenet as face recognition model. The representation must be
        unique and it is stored in the Azure storage
            - img:      a base64 encoded image that must contain a single face
            - username: the username that represent a univoque identity of the input face
            - info:     additional info about the identity
        Returns:        a message that determines the status of the request
    """
    message = {'message': NO_JSON_MESSAGE}

    if request.is_json:
        # Dictionary that represent the input argument
        input_arg: dict = loads(request.get_data())

        if input_arg is None:
            return jsonify({'message': EMPTY_MESSAGE})

        # Get the input value from the json string 
        img: str = input_arg.get('img')
        username: str = input_arg.get('username')
        info: str = input_arg.get('info')

        is_input_correct, message = _check_represent_input(img, username, info, message)

        # Process the image to find the representation only if the input values are correct
        if is_input_correct is True:
            if _create_temporary_image_from_b64(img):
                message = upload_representation(TEMP_IMG, username, info)
            else:
                return jsonify({'message': BASE64_ERROR_MESSAGE})

            if isfile(TEMP_IMG):
                remove(TEMP_IMG)  # clean temporary file

    return jsonify(message)


@app.route('/find', methods=['POST'])
def find():
    """
        This method is used to find the representation with the closest representation
        to the input one.
        - img:      the input image encoded in base64
        - Returns:  a message with the status of the request. If successful the username and info
                    of the representation found are added to the response.
    """
    message = {'message': NO_JSON_MESSAGE}

    if request.is_json:
        input_arg: dict = loads(request.get_data())

        # No arguments passed
        if input_arg is None:
            return jsonify({'message': EMPTY_MESSAGE})

        img: str = input_arg.get('img')

        # Wrong input: img not setted or empty
        if img is None or not img:
            return jsonify({'message': 'wrong argument passed'})

        if _create_temporary_image_from_b64(img):
            message = find_representations(TEMP_IMG)
        else:
            return jsonify({'message': BASE64_ERROR_MESSAGE})

        if isfile(TEMP_IMG):
            remove(TEMP_IMG)  # clean temporary file

    return jsonify(message)


def _check_represent_input(img, username, info, message):
    # Check if the input misses input parameters
    if (img is None) or (username is None) or (info is None):
        message = {'message': ALL_VALUES_NOT_PASSED_MESSAGE}
        return False, message

    # Check if one the string is empty
    if (not img) or (not username) or (not info):
        message = {'message': 'Some values are empty!'}
        return False, message

    return True, message


def _create_temporary_image_from_b64(img):
    # Wrap image extraction in a try-except to avoid error on base64 image
    try:
        # Create a local temporary file, decoding the input base64 image
        with open(TEMP_IMG, 'wb') as f:
            f.write(b64decode(img.encode('utf-8')))
    except Error:
        return False

    return True


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
