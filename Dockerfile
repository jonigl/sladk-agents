FROM python:3.12-alpine
ARG USERNAME=adk

WORKDIR /opt/app



COPY . .
RUN pip3 install -r requirements.txt
RUN ruff check .
RUN ruff format --check .

RUN adduser -D $USERNAME
RUN chown -R $USERNAME /opt/app
USER $USERNAME

ENTRYPOINT python3 app.py
