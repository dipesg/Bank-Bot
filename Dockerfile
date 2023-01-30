FROM python:3.7-slim

WORKDIR /app
COPY . .

#COPY requirements.txt requirements.txt
USER root

RUN pip install -r requirements.txt

RUN rasa train

#VOLUME /app/models
#set entrypoint for interactive shell
ENTRYPOINT ["rasa"]

#COMMAND TO RUN WHEN CONTAINER STARTS
CMD [ "run","-m","/app/models","--enable-api", "--port", "8080"]
