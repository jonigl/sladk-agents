FROM python:3.12-alpine
ARG USERNAME=adk

WORKDIR /opt/app

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt
COPY . .

RUN adduser -D $USERNAME
RUN chown -R $USERNAME /opt/app
USER $USERNAME

ENTRYPOINT ["python3", "app.py"]
