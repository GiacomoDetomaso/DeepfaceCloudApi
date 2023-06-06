# DeepFaceCloudApi
The DeepFaceCloudApi is the project on which my bachelor thesis in **Computer Science** is based of. It is developed under the subject of **Software Engineering**, and provides a REST api service for the face recognition framework developed by Serengil called Deepface.

## Project goals
The main goals of this project are the followings: 
1. Provide an API to the Deepface framework that is ready to be deployed in every cloud platform such as Azure, AWS, GCP and more
2. Provide all the services needed to perform face recognition's tasks
3. Provide a maintainable software architecture

## Services
The API is developed using Python adn Flask module to handle http requests. It provides the following services:
- Face coordinates extraction
- Face boxes extraction
- Registration of a face providing a unique username and some additional informations
- **Face identification task**: find all the known faces (with the linked data associated) in the input image
- **Face verification task**: assert that the input image contains the identity specified by the provided username

| Service                          | Endpoint            | Method |
| ---------------------------------| --------------------| ------ |
| Face coordinates extraction      | /detect/coordinates | POST   |
| Face boxes extraction            | /detect/faceboxes   | POST   |
| Face representation registration | /represent          | POST   |
| Face identification              | /find               | POST   |
| Face verification                | /verify             | POST   |
