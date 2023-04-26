from flask import Flask, render_template, request, jsonify
from deepface.DeepFace import represent as get_embeddings
from json import loads
from base64 import b64decode
from modules.blobs import BlobManager

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/imgup', methods=['POST'])
def imgup():
    '''
        This API is used to load an image to the azure blob storage service.
        It takes in input a json request wit three parameters:
            - b64: an encoded base64 image
            - file_name: the name of the file that will be created on the storage
            - ext: the extension of the file 
        Returns a message with the status of the request
    '''
    return_message = dict()

    if request.is_json:
        print("--- Json request type")
        try:
            # Loads the json input as a dictionary and get the data string
            json_input: dict = loads(request.get_json(cache=False))

            if json_input is None:
                return {'message': 'empty input set passed'}

            # Get the requests input parameters
            b64: str = json_input.get('b64', None)
            file_name: str = json_input.get('file_name', None)
            ext: str = json_input.get('ext', None)

            file_name_complete = file_name + ext

            # Create a new file from the encoded string b64. 
            with open(file_name_complete, 'wb') as f:
                f.write(b64decode(b64.encode('ascii')))

            print("--- Temp file created: ", f.name) 

            blob_manager = BlobManager('dfdb')

            # Execute the blob manager operation. If there are some errors an exception will be thrown
            try:
                blob_manager.upload_blob(f.name)
            except ValueError:
                return_message = {'res': 'fail', 'message': 'Impossible to save the encoded image. Check the b64 field format.'}
            
            # At this point the file has been saved so a success message is written
            return_message = {'res' : 'ok', 'message': 'The image has been correctly saved'}

        except OSError:
            print('--- OSError')
            return_message = {'res': 'fail', 'message': 'Impossible to save the encoded image. Check the b64 field format.'}
    else:
        print("-- No JSON format")
        return_message = {'res': 'fail', 'message': 'The content type of the request is not application/json'}

    return jsonify(return_message)

@app.route('/represent', methods=['POST'])
def represent():
    '''
        This method gives a representation of the face in the input image
        using Facenet as face recognition model.
            - img: a base64 encoded image that must contain a single face
            - username: the username that represent a univoque identity of the input face
            - info: additional info about the identity
        Returns: 
            - the representation of the face in terms of embedding inside a json response or an error message
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
            try:
                with open('prova.jpg', 'wb') as f:
                    f.write(b64decode(img.encode('utf-8')))

                # Pass the base64 image to the represent function
                representation: dict = get_embeddings(img_path=f.name, detector_backend='ssd', model_name='Facenet')

                # The base image must contain just one face
                if len(representation) > 1:
                    message = {'message': 'The image must contain a single face picture. This error could happen if false positives are detected.'} 
                else: 
                    embegging = representation[0]['embedding'] # extracts the face embedding
                    facial_area = representation[0]['facial_area'] # extract face box coordinates

                    # Write a success message, putting the representations and the face coordinates
                    message = {
                        'message': 'Success. This Json stores the representation requested',
                        'representation': embegging,
                        'x1': facial_area['x'],
                        'y1': facial_area['y'],
                        'x2': facial_area['x'] + facial_area['w'],
                        'y2': facial_area['y'] + facial_area['h']
                    }
            except ValueError:
                message = {'message': 'Cannot find any representation for the given image'} 
            except OSError:
                message = {'message': 'The input image is not a base64 image'}

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