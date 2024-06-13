FROM python:3.8

EXPOSE 8080
WORKDIR /app

ARG PROJECT_ID
ENV PROJECT_ID=${PROJECT_ID}

COPY . ./

RUN pip install -r requirements.txt

ENTRYPOINT streamlit run app.py --server.port=8080 --server.address=0.0.0.0 -- --project $(echo ${PROJECT_ID})