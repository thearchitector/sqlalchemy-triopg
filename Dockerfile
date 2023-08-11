FROM python:3.11

WORKDIR /triopg

RUN apt-get update && \
    apt-get -y install vim && \
    pip install pdm

COPY . .

RUN pdm export -G :all -o req.txt && \
    pip install -r req.txt

CMD [ "tail", "-f", "/dev/null" ]
