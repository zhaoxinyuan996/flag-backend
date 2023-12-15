import threading

from app import app
from common.job import DelayJob
from util.config import dev

if __name__ == '__main__':
    if not dev:
        threading.Thread(target=DelayJob.run).start()
    app.run()
