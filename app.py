from flask import Flask, render_template, request, jsonify
from json import loads
from base64 import b64decode
from os import remove
from os.path import isfile
from binascii import Error

from modules.services import (
    # import common keys of json replies
    KEY_STATUS, KEY_MESSAGE, KEY_COORDINATES, KEY_IMG_B64,
    # import common status 
    STATUS_FAIL, STATUS_SUCCESS, 
    # import common messages
    NO_JSON_MESSAGE, EMPTY_MESSAGE, ALL_VALUES_NOT_PASSED_MESSAGE, BASE64_ERROR_MESSAGE,
    # import a costant with the name of temporary image
    TEMP_IMG,
    # import json requests param values
    JSON_IMG, JSON_USERNAME, JSON_INFO, JSON_IDENTITY,
    # import the services of the facade
    upload_representation, find_representations, verify_representation, extract_faces  
)

app = Flask(__name__)


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/detect/coordinates', methods=['POST'])
def detect_coordinates():
    """
        This method is used to detect the coordinates of a face into the input image
            - img:  the image in which the face will be detected
    """
    message = {KEY_MESSAGE: NO_JSON_MESSAGE, 
               KEY_STATUS: STATUS_FAIL}

    if request.is_json and request.data:
        input_arg: dict = loads(request.get_data())

        if input_arg is None:
            return jsonify({KEY_MESSAGE: EMPTY_MESSAGE,
                            KEY_STATUS: STATUS_FAIL})

        # Get the input value from the json string 
        img: str = input_arg.get(JSON_IMG)

        # Check the input correctness
        if img is None or not img:
            return jsonify({KEY_MESSAGE: 'img Field must be present and be not empty',
                            KEY_STATUS: STATUS_FAIL})

        if _create_temporary_image_from_b64(img):
            try:
                coordinates = extract_faces(TEMP_IMG)

                message = {KEY_MESSAGE: 'Coordinates found',
                           KEY_STATUS: STATUS_SUCCESS,
                           KEY_COORDINATES: coordinates}
            except ValueError:
                message = {KEY_MESSAGE: 'Could not detect any face in the given image',
                           KEY_STATUS: STATUS_FAIL}

        if isfile(TEMP_IMG):
            remove(TEMP_IMG)  # clean temporary file

    return jsonify(message)


@app.route('/detect/faceboxes', methods=['POST'])
def detect_faceboxes():
    """
        This method is used to detect the coordinates of a face into the input image
            - img:  the image in which the face will be detected
    """
    message = {KEY_MESSAGE: NO_JSON_MESSAGE,
               KEY_STATUS: STATUS_FAIL}

    if request.is_json and request.data:
        input_arg: dict = loads(request.get_data())

        if input_arg is None:
            return jsonify({KEY_MESSAGE: EMPTY_MESSAGE})

        # Get the input value from the json string 
        img: str = input_arg.get(JSON_IMG)

        # Check the input correctness
        if img is None or not img:
            return jsonify({KEY_MESSAGE: 'img Field must be present and be not empty'})

        if _create_temporary_image_from_b64(img):
            try:
                b64_img = extract_faces(TEMP_IMG, return_image=True)
                message = {KEY_MESSAGE: 'Face detected',
                           KEY_STATUS: STATUS_SUCCESS,
                           KEY_IMG_B64: b64_img}
            except ValueError:
                message = {KEY_MESSAGE: 'Could not detect any face in the given image',
                           KEY_STATUS: STATUS_FAIL}

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
    message = {KEY_MESSAGE: NO_JSON_MESSAGE,
               KEY_STATUS: STATUS_FAIL}

    if request.is_json and request.data:
        input_arg: dict = loads(request.get_data())

        if input_arg is None:
            return jsonify({KEY_MESSAGE: EMPTY_MESSAGE,
                            KEY_STATUS: STATUS_FAIL})

        # Get the input value from the json string 
        img: str = input_arg.get(JSON_IMG)
        identity: str = input_arg.get(JSON_IDENTITY)

        # Check the input correctness
        if img is None or identity is None:
            return jsonify({KEY_MESSAGE: ALL_VALUES_NOT_PASSED_MESSAGE,
                            KEY_STATUS: STATUS_FAIL})
        if not img or not identity:
            return jsonify({KEY_MESSAGE: 'Some of the input is empty',
                            KEY_STATUS: STATUS_FAIL})

        if _create_temporary_image_from_b64(img):
            message = verify_representation(TEMP_IMG, identity)
        else:
            return jsonify({KEY_MESSAGE: BASE64_ERROR_MESSAGE,
                            KEY_STATUS: STATUS_FAIL})

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
    message = {KEY_MESSAGE: NO_JSON_MESSAGE,
               KEY_STATUS: STATUS_FAIL}

    if request.is_json and request.data:
        # Dictionary that represent the input argument
        input_arg: dict = loads(request.get_data())

        if input_arg is None:
            return jsonify({KEY_MESSAGE: EMPTY_MESSAGE,
                            KEY_STATUS: STATUS_FAIL})

        # Get the input value from the json string 
        img: str = input_arg.get(JSON_IMG)
        username: str = input_arg.get(JSON_USERNAME)
        info: str = input_arg.get(JSON_INFO)

        is_input_correct, message = _check_represent_input(img, username, info, message)

        # Process the image to find the representation only if the input values are correct
        if is_input_correct is True:
            if _create_temporary_image_from_b64(img):
                message = upload_representation(TEMP_IMG, username, info)
            else:
                return jsonify({KEY_MESSAGE: BASE64_ERROR_MESSAGE,
                                KEY_STATUS: STATUS_FAIL})

            if isfile(TEMP_IMG):
                remove(TEMP_IMG)  # clean temporary file

    return jsonify(message)


@app.route('/identify', methods=['POST'])
def identify():
    """
        This method is used to find the representation with the closest representation
        to the input one.
        - img:      the input image encoded in base64
        - Returns:  a message with the status of the request. If successful the username and info
                    of the representation found are added to the response.
    """
    message = {KEY_MESSAGE: NO_JSON_MESSAGE,
               KEY_STATUS: STATUS_FAIL}

    if request.is_json and request.data:
        input_arg: dict = loads(request.get_data())

        # No arguments passed
        if input_arg is None:
            return jsonify({KEY_MESSAGE: EMPTY_MESSAGE,
                            KEY_STATUS: STATUS_FAIL})

        img: str = input_arg.get(JSON_IMG)

        # Wrong input: img not setted or empty
        if img is None or not img:
            return jsonify({KEY_MESSAGE: 'wrong argument passed',
                            KEY_STATUS: STATUS_FAIL})

        if _create_temporary_image_from_b64(img):
            message = find_representations(TEMP_IMG)
        else:
            return jsonify({KEY_MESSAGE: BASE64_ERROR_MESSAGE,
                            KEY_STATUS: STATUS_FAIL})

        if isfile(TEMP_IMG):
            remove(TEMP_IMG)  # clean temporary file

    return jsonify(message)


def _check_represent_input(img, username, info, message):
    # Check if the input misses input parameters
    if (img is None) or (username is None) or (info is None):
        message = {KEY_MESSAGE: ALL_VALUES_NOT_PASSED_MESSAGE,
                   KEY_STATUS: STATUS_FAIL}
        return False, message

    # Check if one the string is empty
    if (not img) or (not username) or (not info):
        message = {KEY_MESSAGE: 'Some values are empty!',
                   KEY_STATUS: STATUS_FAIL}
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
