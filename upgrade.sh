#!/bin/sh
git pull;
docker-compose down;
docker-compose up -d --build;
docker inspect --format '{{ .NetworkSettings.IPAddress }}' zoloto_viewer_postgres_1;
