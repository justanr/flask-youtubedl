#!/bin/bash
set -e

case $1 in
    celery)
        shift
        exec fytdl celery worker
        ;;
    *)
        echo "Unknown input!"
        ;;
esac
