#!/bin/bash
set -e

fytdl create-db

case $1 in
    celery)
        shift
        exec fytdl celery worker
        ;;
    *)
        echo "Unknown input!"
        ;;
esac
