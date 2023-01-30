FROM rasa/rasa-sdk:3.3.0
WORKDIR /app
COPY requirements.txt requirements.txt
USER root
RUN pip install -r requirements.txt
EXPOSE 5055
USER 1001