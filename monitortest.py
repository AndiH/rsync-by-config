#!/usr/bin/env python3
import sys
import time
import logging


try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler

    thereIsWatchDog = True
except ImportError:
    thereIsWatchDog = False
    print("No Watchdog!")

if thereIsWatchDog:
    class anyEventHandler(FileSystemEventHandler):
        def __init__(self, something = None):
            super(anyEventHandler, self).__init__()
            self.some = something
        def on_any_event(self, event):
            super(anyEventHandler, self).on_any_event(event)

            print("Event!")

def printSomething(astring = "Hello"):
    print(astring)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    path = sys.argv[1] if len(sys.argv) > 1 else '.'
    # event_handler = LoggingEventHandler()
    a = lambda: printSomething("Yo")
    event_handler = anyEventHandler(something = a)
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping...")
        observer.stop()
    observer.join()
