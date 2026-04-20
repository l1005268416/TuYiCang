import os
import time
import logging
from queue import Queue, Empty
from threading import Thread, Lock
from concurrent.futures import ThreadPoolExecutor, as_completed
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logger = logging.getLogger(__name__)


class DirectoryEventHandler(FileSystemEventHandler):
    def __init__(self, handler_fn, valid_extensions=None, event_queue=None):
        super().__init__()
        self.handler_fn = handler_fn
        if valid_extensions is None:
            valid_extensions = {'jpg', 'jpeg', 'png', 'webp', 'bmp'}
        self.valid_extensions = valid_extensions
        self.event_queue = event_queue or Queue()
        self._processing_lock = Lock()

    def _is_image(self, file_path):
        ext = os.path.splitext(file_path)[1].lower().lstrip('.')
        return ext in self.valid_extensions

    def on_created(self, event):
        if not event.is_directory and self._is_image(event.src_path):
            time.sleep(1)
            self.event_queue.put(('created', event.src_path))

    def on_modified(self, event):
        if not event.is_directory and self._is_image(event.src_path):
            time.sleep(1)
            self.event_queue.put(('modified', event.src_path))

    def on_deleted(self, event):
        if not event.is_directory and self._is_image(event.src_path):
            self.event_queue.put(('deleted', event.src_path))


class WatcherService:
    def __init__(self, config_manager, handler_fn):
        self.config = config_manager
        self.handler_fn = handler_fn
        self._observer = None
        self._worker_thread = None
        self._event_queue = Queue()
        self._running = False
        self._executor = None

    def start(self, photo_root_path=None):
        if self._running:
            return {"status": "running"}

        if photo_root_path is None:
            photo_root_path = self.config.get_value('core.photo_root_path')

        if not os.path.isdir(photo_root_path):
            return {"status": "failed", "error": f"Directory not found: {photo_root_path}"}

        max_workers = self.config.get_value('performance.max_concurrent_requests') or 4
        self._executor = ThreadPoolExecutor(max_workers=max_workers)

        valid_extensions = self.config.get_value('preprocessing.valid_extensions')
        event_handler = DirectoryEventHandler(
            self.handler_fn,
            valid_extensions=valid_extensions,
            event_queue=self._event_queue
        )

        self._observer = Observer()
        self._observer.schedule(event_handler, photo_root_path, recursive=True)
        self._observer.start()
        self._running = True

        self._worker_thread = Thread(target=self._process_events, daemon=True)
        self._worker_thread.start()

        logger.info("File watcher started for: %s", photo_root_path)
        return {"status": "running"}

    def stop(self):
        if self._observer:
            self._observer.stop()
            self._observer.join(timeout=5)
        self._running = False
        if self._executor:
            self._executor.shutdown(wait=True)
        logger.info("File watcher stopped")
        return {"status": "stopped"}

    def _process_events(self):
        while self._running:
            try:
                event = self._event_queue.get(timeout=1)
                event_type, file_path = event
                logger.info("event_queue size: %s, event_type: %s, file_path: %s", self._event_queue.qsize(), event_type, file_path)
                if self.handler_fn and self._executor:
                    self._executor.submit(self.handler_fn, event_type, file_path)
                self._event_queue.task_done()
            except Empty:
                continue
            except Exception as e:
                logger.error("Event processing error: %s", e)
