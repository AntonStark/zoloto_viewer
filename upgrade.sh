#!/bin/sh
git pull || exit 1;
docker-compose down;
docker-compose up -d --build;
docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' zoloto_viewer_postgres_1;
