FROM python:3.11-bullseye
LABEL version="1.1a"

RUN mkdir /home/wybory

ADD requirements.txt /tmp/requirements.txt
ADD candidates.txt /home/wybory/candidates.txt
ADD strings.txt /home/wybory/strings.txt
ADD app /home/wybory/app
ADD static /home/wybory/static
ADD templates /home/wybory/templates
COPY runner.py /home/wybory/runner.py

RUN useradd wybory
RUN chown -R wybory:wybory /home/wybory
USER wybory

RUN pip install -r /tmp/requirements.txt

WORKDIR /home/wybory
CMD ["python", "-m", "uvicorn", "runner:app", "--host", "0.0.0.0"]