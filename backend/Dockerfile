FROM python:3.8.5

WORKDIR /code
COPY . /code
RUN pip install -r /code/requirements.txt --no-cache-dir
RUN chmod ugo+x entrypoint.sh
CMD sh entrypoint.sh