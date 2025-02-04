FROM python:3.9.7
WORKDIR /dev-app/
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
COPY ./requirements.txt .
RUN pip install -r requirements.txt --no-cache-dir
COPY . .
ENTRYPOINT ["sh", "/dev-app/entrypoint.sh"]
