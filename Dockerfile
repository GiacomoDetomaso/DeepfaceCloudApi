FROM python:3

# create the docker app folder to run the api
RUN mkdir app
# select app as working dir
WORKDIR /app
#install dependencies and update the system
RUN apt-get update
RUN apt install libgl1-mesa-glx -y
RUN apt-get install ffmpeg libsm6 libxext6 -y
# copy the content of the project folder into the docker app folder
COPY . /app
# copy the requirementes to the folder
COPY ./requirements.txt /app/
# install python packages via requirements file
RUN pip install -r requirements.txt
# expose the port used to run the flask server
EXPOSE 5000
# select the entry point of cmd command and start the app
ENTRYPOINT ["python3"]
CMD [ "app.py" ]