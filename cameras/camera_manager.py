import threading

from cameras.camera import CameraProcessor


class CameraManager:

    def __init__(self):

        self.cameras = {}

        self.lock = threading.Lock()

    def add_camera(
        self,
        camera_id,
        name,
        location,
        stream_url
    ):

        with self.lock:

            if camera_id in self.cameras:
                return

            processor = CameraProcessor(
                camera_id,
                name,
                location,
                stream_url
            )

            self.cameras[
                camera_id
            ] = processor

            processor.start()

    def remove_camera(
        self,
        camera_id
    ):

        with self.lock:

            camera = self.cameras.get(
                camera_id
            )

            if camera:
                camera.stop()

                del self.cameras[
                    camera_id
                ]

    def get_camera(
        self,
        camera_id
    ):

        return self.cameras.get(
            camera_id
        )

    def get_frame(
        self,
        camera_id
    ):

        camera = self.get_camera(
            camera_id
        )

        if not camera:
            return None

        return camera.get_frame()

    def stop_all(self):

        with self.lock:

            for camera in self.cameras.values():
                camera.stop()

            self.cameras.clear()