import zmq
from gym_everglades.resources import evgtypes, evgcommands
from inspect import getmembers
from logging import getLogger
from uuid import uuid4
from time import sleep
import json

logger = getLogger()


class Connection:
    def __init__(self, pub_addr, sub_addr, tag, await_connection_time=60):
        """
        Maintains connection to server
        :param pub_addr: publish socket address
        :param sub_addr: subscribe socket address
        :param tag: name of the connection
        :param await_connection_time: how long to wait for the server to respond in seconds
        """
        self.__pub_addr = pub_addr
        self.__sub_addr = sub_addr
        self.__await_connection_time = await_connection_time
        self.tag = tag
        self.__session_token = None

        self.__pub_context = zmq.Context()
        self.__pub_socket = self.__pub_context.socket(zmq.PUB)
        self.__pub_socket.bind(self.__pub_addr)

        self.__sub_context = zmq.Context()
        self.__sub_socket = self.__sub_context.socket(zmq.SUB)
        self.__sub_socket.connect(self.__sub_addr)
        self.__sub_socket.setsockopt(zmq.SUBSCRIBE, b"")

        self.connect()

        # Handles special case command types without a from message function
        def make(cls):
            def _make(*args, **kwargs):
                return cls()

            return _make

        # Store function for creating each message class by message type
        self.__parsers = {}
        for name, cls in getmembers(evgtypes):
            type_id = getattr(cls, "TypeId")
            from_message = getattr(cls, "from_message", make(cls))
            if callable(type_id):
                self.__parsers[type_id()] = from_message

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"Connection for {self.tag}\n\tPub addr: {self.__pub_addr}\n\tSub addr: {self.__sub_addr}"

    def connect(self):
        """
        Establish connection to server
        :return:
        """
        guid = uuid4()
        self.send(evgcommands.HelloWorld(guid, self.tag))

        counter = -1
        while counter < self.__await_connection_time:
            if self.__await_connection_time != 0:
                counter += 1
            msgs = self.receive_all()
            msg_objs = [self.parse_message(x) for x in msgs]
            for msg_obj in msg_objs:
                if isinstance(msg_obj, evgtypes.NewClientACK) and msg_obj.guid == guid:
                    self.__session_token = msg_obj.ses_tok
                    logger.debug(f'Connected to server ({self.__session_token}')
                    return
            sleep(0.25)
            logger.debug(f'Waiting for server connection. Attempt {counter}')
            self.send(evgcommands.HelloWorld(guid, self.tag))

        raise Exception(f'Unable to connect to server after {counter} seconds. Exiting...')

    def close(self):
        self.__session_token = None
        self.__pub_socket.close()
        self.__pub_context.destroy()
        self.__pub_context.term()
        self.__sub_socket.close()
        self.__sub_context.destroy()
        self.__sub_context.term()

    def receive_all(self):
        msgs = []
        while self.__sub_socket.poll(100) == zmq.POLLIN:
            msgs.append(self.receive())

        return msgs

    def receive(self):
        try:
            [addr, data] = self.__sub_socket.recv_multipart(flags=zmq.NOBLOCK)
        except Exception as e:
            logger.exception(f'Failed to receive msg\n{e}')
            return {}  # NOTE this may need to be a list
        return json.loads(data)  # old docs indicate this returns a list

    def send(self, msg):
        # TODO: does this still need the 'BF" prefix?
        self.__pub_socket.send_multipart([b"BF", msg.encode('utf-8')])

    def parse_message(self, msg):
        """
        Creates corresponding message class based on message's type
        :param msg: the message obj received over the line
        :return: message class object
        """
        try:
            return self.__parsers[msg['type']](msg)
        except KeyError as e:
            logger.exception("Failed to parse message: {} of type {}\n{}".format(
                msg, msg.get('type', 'N/A'), e
            ))
        except Exception as e:
            raise e

    def receive_and_parse(self):
        return [self.parse_message(msg) for msg in self.receive_all()]
