#!/usr/bin/env python3

import sys
import logging
import requests
from pathlib import Path

FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
logging.basicConfig(format=FORMAT, level=logging.DEBUG)
formatter = logging.Formatter(FORMAT)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

logging.getLogger("requests").setLevel(logging.DEBUG)
logging.getLogger("urllib3").setLevel(logging.DEBUG)

from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QCoreApplication, QFile, QIODevice
from PySide6.QtCore import QObject, QThread, Signal

from q_text_logger import *

class ProxyChecker(QObject):

    finished = Signal()

    def __init__(self, url, username, password, proxies):
        super().__init__()
        self._url = url
        self._username = username
        self._password = password
        self._proxies = proxies

    def run(self):

        url = self._url
        username = self._username
        password = self._password
        proxies = self._proxies

        logger.info("Started")
        logger.debug(f"Url:      '{url}'")
        logger.debug(f"Username: '{username}'")
        logger.debug(f"Password: '{password}'")
        logger.debug(f"Proxies:  '{proxies}'")

        if username and password:
            proxyUrlPrefix = f"{username}:{password}@"
        elif username:
            proxyUrlPrefix = f"{username}@"
        else:
            proxyUrlPrefix = ""

        for proxy in proxies:
            proxy = proxy.strip()
            if proxy.startswith("#"):
                logger.info(proxy)
                continue
            requestProxies = {
                "http": f"http://{proxyUrlPrefix}{proxy}/",
                "https": f"http://{proxyUrlPrefix}{proxy}/",
            }
            if not proxy:
                proxy = "no-proxy"
                requestProxies = None
            logger.debug(f"Checking: {requestProxies}")
            try:
                res = requests.get(url=url, proxies=requestProxies, timeout=1)
                logger.info(f"{proxyUrlPrefix}{proxy} - {res.status_code}")
            except requests.RequestException as e:
                logger.error(f"{proxyUrlPrefix}{proxy} - {e}")

        logger.info("Done")
        self.finished.emit()

def checkButtonClicked():
    global window

    url = window.inputUrl.text()
    username = window.inputUsername.text()
    password = window.inputPassword.text()
    proxies = window.inputProxies.toPlainText().split("\n")
    proxies = list(filter(lambda x: x, map(lambda x: x.strip(), proxies)))
    proxies.insert(0, '')

    window.workerThread = QThread()
    window.worker = ProxyChecker(url, username, password, proxies)
    window.worker.moveToThread(window.workerThread)

    window.worker.finished.connect(window.workerThread.quit)
    window.worker.finished.connect(window.worker.deleteLater)

    window.workerThread.started.connect(window.worker.run)
    window.workerThread.finished.connect(window.workerThread.deleteLater)

    window.buttonCheck.setEnabled(False)
    window.workerThread.finished.connect(
        lambda: window.buttonCheck.setEnabled(True)
    )

    window.workerThread.start()

def main():
    QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    QCoreApplication.setApplicationName("proxy-checker")
    QCoreApplication.setApplicationVersion("1.0")

    app = QApplication(sys.argv)

    ui_file_name = Path(__file__).resolve().with_name("mainwindow.ui")
    ui_file = QFile(ui_file_name)
    if not ui_file.open(QIODevice.ReadOnly):
        print(f"Cannot open {ui_file_name}: {ui_file.errorString()}")
        return -1

    loader = QUiLoader()
    global window
    window = loader.load(ui_file)
    ui_file.close()
    if not window:
        print(loader.errorString())
        return -1

    if hasattr(window, 'logger'):
        gui_handler = QTextLogger(window.logger)
        gui_handler.setLevel(logger.getEffectiveLevel())
        gui_handler.setFormatter(formatter)
        logging.getLogger().addHandler(gui_handler)
        logger.debug('Added GUI logger')

    logger.debug('Starting')

    window.show()
    window.buttonCheck.clicked.connect(checkButtonClicked)

    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
