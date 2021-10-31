FROM docker.io/python:3.9

RUN mkdir /app
WORKDIR /app

COPY satisfactory_docker_ui ./satisfactory_docker_ui
COPY pyproject.toml ./pyproject.toml

RUN pip3 install poetry
RUN poetry install

WORKDIR /app/satisfactory_docker_ui
CMD ["poetry", "run", "gunicorn", "-w4", "-b0.0.0.0:5000", "wsgi:app"]