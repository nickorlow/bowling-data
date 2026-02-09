FROM python:3.11-slim-buster as build-env

WORKDIR /site
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt 
COPY . .
RUN mkdir gen-html
RUN python3 src/main.py
RUN mkdir out 
RUN cp -r ./assets/* ./gen-html/
RUN cp -r ./gen-html/* ./out/

FROM ghcr.io/nickorlow/anthracite:0.2.1
COPY --from=build-env /site/out/ /www/
#FROM nginx:alpine
COPY --from=build-env /site/out/ /usr/share/nginx/html
