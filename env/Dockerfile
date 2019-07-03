#FROM python:3.6-slim-stretch
FROM python:3.6-stretch

RUN pip install -U pip setuptools
RUN pip install numpy gym pyzmq

RUN mkdir gym-everglades/

COPY ./gym-everglades ./gym-everglades

RUN pip install -e gym-everglades/

ENV PYTHONPATH "${PYTHONPATH}:/gym-everglades"