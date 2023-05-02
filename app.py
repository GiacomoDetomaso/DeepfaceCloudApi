from flask import Flask, render_template, request, jsonify
from json import loads
from base64 import b64decode
from os import remove
from modules.operations import FaceRepresentation, FaceRepresentationManager

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/represent', methods=['POST'])
def represent():
    '''
        This method gives a representation of the face in the input image
        using Facenet as face recognition model.
            - img: a base64 encoded image that must contain a single face
            - username: the username that represent a univoque identity of the input face
            - info: additional info about the identity
        Returns: 
            - a message that determines the status of the request
    '''
    message = {'message': 'You must send a json request, or request you have sent is empty'}

    if request.is_json:
        # Dictionary that represent the input argument
        input_arg: dict = loads(request.get_data())

        if input_arg is None:
           return {'message': 'empty input set passed'}
       
        # Get the input value from the json string 
        img: str = input_arg.get('img')
        username: str = input_arg.get('username')
        info: str = input_arg.get('info')

        is_input_correct, message = _check_represent_input(img, username, info, message)
        
        # Execute all the processing of the image to find the representation only 
        # if the input values are correct
        if is_input_correct is True:

            with open('img.jpg', 'wb') as f:
                f.write(b64decode(img.encode('utf-8')))

            face_representation = FaceRepresentation(username, info)

            if face_representation.generate_representation_single_face(f.name, 'retinaface', 'Facenet'):
                manager = FaceRepresentationManager.init_upload(face_representation)

                if manager.upload_representation():
                    message = {'message': 'Representation generated'}
                else:
                    message = {'message': 'Representation not generated: duplicated username'}
            else:
                message = {'message': 'Could not create a representation: no face or multiple faces detected'}

            remove(f.name)

    return jsonify(message)

@app.route('/find', methods=['POST'])
def find():
    message = {'message': 'You must send a json request, or request you have sent is empty'}

    if request.is_json:
        input_arg: dict = loads(request.get_data())

        # No arguments passed
        if input_arg is None:
           return {'message': 'empty input set passed'}
        
        img: str = input_arg.get('img')

        # Wrong input
        if img is None or not img:
            return {'message': 'wrong argument passed'}

        # TODO: CHECK IMAGE INPUT
        # Decode the image from the base64 format and create the temp file
        with open('img.jpg', 'wb') as f:
            f.write(b64decode(img.encode('utf-8')))

        rep = FaceRepresentation()

        if rep.generate_representation_single_face(f.name, 'retinaface', 'Facenet'):
            manager = FaceRepresentationManager.init_upload(rep)
            rep = manager.find_closest_representation()
        else:
            rep = None

        if rep is None:
            message = {'message': 'Cannot find any close representation'}
        else:
            message = {'message': 'Success!', 'username': rep.username, 'info': rep.info}

        remove(f.name)

    return jsonify(message)

def load_json_request(req) -> dict:
    if type(req) == 'dict':
        return req
    else:
        return loads(req)

def _check_represent_input(img, username, info, message):
    # Check if the input misses input parameters
    if (img is None) or (username is None) or (info is None):
        message = {'message': 'You must pass all values in order to perform this action'} 
        return False, message

    # Check if one the string is empty
    if (not img) or (not username) or (not info):
        message = {'message': 'Some values are empty!'} 
        return False, message
    
    return True, message

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)