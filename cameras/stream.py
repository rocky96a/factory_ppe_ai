import cv2
import time


class CameraStream:

    def __init__(self, source):
        self.source = source
        self.capture = None
        self._open()

    def _open(self):

        # Laptop / USB webcam
        if isinstance(self.source, int):
            print(f"[STREAM] Opening webcam /dev/video{self.source}")

            self.capture = cv2.VideoCapture(
                self.source,
                cv2.CAP_V4L2
            )

            # Fallback
            if not self.capture.isOpened():
                print("[STREAM] V4L2 failed, trying default OpenCV backend")
                self.capture.release()
                self.capture = cv2.VideoCapture(self.source)

        # RTSP / IP camera
        else:
            print(f"[STREAM] Opening RTSP: {self.source}")

            self.capture = cv2.VideoCapture(
                self.source,
                cv2.CAP_FFMPEG
            )

        if self.capture is not None:
            self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    def is_opened(self):
        return (
            self.capture is not None
            and self.capture.isOpened()
        )

    def read(self):

        if not self.is_opened():
            self._open()

            if not self.is_opened():
                return False, None

        ret, frame = self.capture.read()

        if ret and frame is not None:
            return True, frame

        return False, None

    def reconnect(self):

        self.release()

        time.sleep(1)

        self._open()

    def release(self):

        if self.capture is not None:
            self.capture.release()
            self.capture = None
