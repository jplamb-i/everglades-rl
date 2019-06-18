FROM ubuntu:18.04
RUN apt-get update && apt-get install -y libzmq3-dev libnorm-dev libsdl2-dev python python-pip

RUN pip install enum zmq

RUN mkdir data/ SourcePython/

COPY data ./data/
COPY SourcePython ./SourcePython/
COPY everglades .

EXPOSE 5555 5556

CMD ./everglades ./data/GameSetup.json $PWD/SourcePython/