FROM python:3.8.5

WORKDIR /code
COPY . /code
RUN pip install -r /code/requirements.txt --no-cache-dir
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "yatube.wsgi"]