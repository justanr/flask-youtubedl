#!/bin/bash
set -e

case $1 in
    celery)
        shift
        exec celery -A flask_youtubedl.worker.tasks worker
        ;;
    *)
        echo "Unknown input!"
        ;;
esac
