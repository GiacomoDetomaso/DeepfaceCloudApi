from flask import Flask, render_template, request, jsonify
from json import loads
from os import remove
from os.path import isfile
from werkzeug.datastructures import ImmutableDict

from modules.services import (
    # import common keys of json replies
    KEY_STATUS, KEY_MESSAGE, KEY_COORDINATES, KEY_IMG_B64,
    # import common status 
    STATUS_FAIL, STATUS_SUCCESS, 
    # import common messages
    NO_MULTIPART_MESSAGE, EMPTY_MESSAGE, ALL_VALUES_NOT_PASSED_MESSAGE, EXTENSION_NOT_SUPPORTED_MESSAGE,
    # import a costant with the name of content type of the http request
    MULTIPART_FORM_DATA,
    # import the supported file extensions for images
    SUPPORTED_IMAGE_EXTENSIONS,
    # import json requests param values
    FIELD_IMG, FIELD_INFO, FIELD_IDENTITY, 
    # import the services of the facade
    upload_representation, find_representations, verify_representation, extract_faces  
)

app = Flask(__name__)


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/detect/coordinates', methods=['GET'])
def detect_coordinates():
    """
        This method is used to detect the coordinates of a face into the input image
            - img:  the image in which the face will be detected
    """
    message = {KEY_MESSAGE: NO_MULTIPART_MESSAGE, 
               KEY_STATUS: STATUS_FAIL}

    if request.content_type.find(MULTIPART_FORM_DATA) != -1:
        input_arg: ImmutableDict = request.form

        if input_arg is None:
            return jsonify({KEY_MESSAGE: EMPTY_MESSAGE})

        # Get the image file
        img =  request.files.get(FIELD_IMG)

        # Check the input correctness
        if img is None:
            return jsonify({KEY_MESSAGE: 'img Field must be present and be not empty'})
        
        temp_file_name = img.filename
        
        # Check the supported extensions
        if not temp_file_name.lower().endswith(SUPPORTED_IMAGE_EXTENSIONS):
            return jsonify({KEY_MESSAGE: EXTENSION_NOT_SUPPORTED_MESSAGE,
                            KEY_STATUS: STATUS_FAIL})
        
        img.save(temp_file_name) # Save the image as local file

        try:
            coordinates = extract_faces(temp_file_name)

            message = {KEY_MESSAGE: 'Coordinates found',
                        KEY_STATUS: STATUS_SUCCESS,
                        KEY_COORDINATES: coordinates}
        except ValueError:
            message = {KEY_MESSAGE: 'Could not detect any face in the given image',
                           KEY_STATUS: STATUS_FAIL}

        if isfile(temp_file_name): remove(temp_file_name)  # clean temporary file

    return jsonify(message)


@app.route('/detect/faceboxes', methods=['GET'])
def detect_faceboxes():
    """
        This method is used to detect the coordinates of a face into the input image
            - img:  the image in which the face will be detected
    """
    message = {KEY_MESSAGE: NO_MULTIPART_MESSAGE,
               KEY_STATUS: STATUS_FAIL}

    if request.content_type.find(MULTIPART_FORM_DATA) != -1:
        input_arg: ImmutableDict = request.form

        if input_arg is None:
            return jsonify({KEY_MESSAGE: EMPTY_MESSAGE})

        # Get the image file
        img =  request.files.get(FIELD_IMG)

        # Check the input correctness
        if img is None:
            return jsonify({KEY_MESSAGE: 'img Field must be present and be not empty'})
        
        temp_file_name = img.filename
        
        # Check the supported extensions
        if not temp_file_name.lower().endswith(SUPPORTED_IMAGE_EXTENSIONS):
            return jsonify({KEY_MESSAGE: EXTENSION_NOT_SUPPORTED_MESSAGE,
                            KEY_STATUS: STATUS_FAIL})
        
        img.save(temp_file_name) # Save the image as local file

        try:
            b64_img = extract_faces(temp_file_name, return_image=True)
            message = {KEY_MESSAGE: 'Face detected',
                        KEY_STATUS: STATUS_SUCCESS,
                        KEY_IMG_B64: b64_img}
        except ValueError:
            message = {KEY_MESSAGE: 'Could not detect any face in the given image',
                        KEY_STATUS: STATUS_FAIL}

        if isfile(temp_file_name): remove(temp_file_name)  # clean temporary file

    return jsonify(message)


@app.route('/verify', methods=['POST'])
def verify():
    """
        This method verifies that the input image contains the person identified
        by a username.
            - img:      a base64 encoded image that must contains a single face to be verfied
            - identity: the stored id of the person searched in the img
    """
    message = {KEY_MESSAGE: NO_MULTIPART_MESSAGE,
               KEY_STATUS: STATUS_FAIL}
    
    if request.content_type.find(MULTIPART_FORM_DATA) != -1:
        input_arg: ImmutableDict = request.form

        if input_arg is None:
            return jsonify({KEY_MESSAGE: EMPTY_MESSAGE,
                            KEY_STATUS: STATUS_FAIL})
        
        # Get the input value from the form fields 
        identity: str = input_arg.get(FIELD_IDENTITY)

        # Read the image from the request
        img = request.files.get(FIELD_IMG)
        
        # Input could not be empty
        if img is None or identity is None:
            return jsonify({KEY_MESSAGE: ALL_VALUES_NOT_PASSED_MESSAGE,
                            KEY_STATUS: STATUS_FAIL})
        
        # Identity could not be an empty string
        if not identity:
                return jsonify({KEY_MESSAGE: 'Identity field has not been setted',
                                KEY_STATUS: STATUS_FAIL})
        
        temp_file_name = img.filename
        
        # Check the supported extensions
        if not temp_file_name.lower().endswith(SUPPORTED_IMAGE_EXTENSIONS):
            return jsonify({KEY_MESSAGE: EXTENSION_NOT_SUPPORTED_MESSAGE,
                            KEY_STATUS: STATUS_FAIL})
        
        img.save(temp_file_name) # Save the image as local file
        message = verify_representation(temp_file_name, identity)

        # Clean temporary file
        if isfile(temp_file_name): remove(temp_file_name)  

    return jsonify(message)


@app.route('/represent', methods=['POST'])
def represent():
    """
        This method gives a representation of the face in the input image
        using Facenet as face recognition model. The representation must be
        unique and it is stored in the Azure storage
            - img:      base64 encoded image that must contain a single face
            - identity: unique identity of the input face
            - info:     additional info about the identity
        Returns:        a message that determines the status of the request
    """
    message = {KEY_MESSAGE: NO_MULTIPART_MESSAGE,
               KEY_STATUS: STATUS_FAIL}
    
    if request.content_type.find(MULTIPART_FORM_DATA) != -1:
        input_arg: ImmutableDict = request.form

        if input_arg is None:
            return jsonify({KEY_MESSAGE: EMPTY_MESSAGE,
                            KEY_STATUS: STATUS_FAIL})
        
        # Get the input value from the form fields 
        username: str = input_arg.get(FIELD_IDENTITY)
        info: str = input_arg.get(FIELD_INFO)

        # Read the image from the request
        img = request.files.get(FIELD_IMG)

        is_input_correct, message = _check_represent_input(img, username, info, message)

        # Evaluate the input
        if not is_input_correct:
            return jsonify(message)
        
        temp_file_name = img.filename

        # Check the supported extensions
        if not temp_file_name.lower().endswith(SUPPORTED_IMAGE_EXTENSIONS):
            return jsonify({KEY_MESSAGE: EXTENSION_NOT_SUPPORTED_MESSAGE,
                            KEY_STATUS: STATUS_FAIL})

        img.save(temp_file_name) # Save the image as local file
        message = upload_representation(temp_file_name, username, info)
        
        # Clean the temporary file
        if isfile(temp_file_name): remove(temp_file_name)

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
    message = {KEY_MESSAGE: NO_MULTIPART_MESSAGE,
               KEY_STATUS: STATUS_FAIL}

    if request.content_type.find(MULTIPART_FORM_DATA) != -1:
        input_arg: ImmutableDict = request.form

        # No arguments passed
        if input_arg is None:
            return jsonify({KEY_MESSAGE: EMPTY_MESSAGE,
                            KEY_STATUS: STATUS_FAIL})

        img = request.files.get(FIELD_IMG)

        # Wrong input: img not setted or empty
        if img is None:
            return jsonify({KEY_MESSAGE: 'No file has been detected. Pass a file to perform the operation.',
                            KEY_STATUS: STATUS_FAIL})
        
        temp_file_name = img.filename

        # Check the supported extensions
        if not temp_file_name.lower().endswith(SUPPORTED_IMAGE_EXTENSIONS):
            return jsonify({KEY_MESSAGE: EXTENSION_NOT_SUPPORTED_MESSAGE,
                            KEY_STATUS: STATUS_FAIL})
        
        img.save(temp_file_name) # Save the image as local file
        message = find_representations(temp_file_name)

        # Clean temporary file
        if isfile(temp_file_name): remove(temp_file_name)  

    return jsonify(message)


def _check_represent_input(img, username, info, message):
    # Check if the input misses input parameters
    if (img is None) or (username is None) or (info is None):
        message = {KEY_MESSAGE: ALL_VALUES_NOT_PASSED_MESSAGE,
                   KEY_STATUS: STATUS_FAIL}
        return False, message

    # Check if one the string is empty
    if (not username) or (not info):
        message = {KEY_MESSAGE: 'Some values are empty!',
                   KEY_STATUS: STATUS_FAIL}
        return False, message

    return True, message


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
