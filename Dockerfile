FROM python:3.8-slim-buster as build-env

WORKDIR /site
COPY . .
RUN pip install -r requirements.txt 
RUN python3 scorer.py
RUN mkdir out 
RUN cp *.html ./out/

#FROM ghcr.io/nickorlow/anthracite:0.2.1
#COPY --from=build-env /site/out/ /www/
FROM nginx:alpine
COPY --from=build-env /site/out/ /usr/share/nginx/html
