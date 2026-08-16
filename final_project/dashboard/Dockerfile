FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir \
    dash==2.17.0 \
    plotly==5.22.0 \
    dash-bootstrap-components==1.6.0 \
    pandas==2.2.2 \
    numpy==1.26.4 \
    requests==2.32.0 \
    sqlalchemy==2.0.30 \
    psycopg2-binary==2.9.9

COPY . .

EXPOSE 8050
CMD ["python", "app.py"]
