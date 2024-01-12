import dataclasses
import os
import pathlib
import socket
import subprocess
import sys

BASE_INFERENCE_TEMPLATE_PATH = pathlib.Path(__file__).parent / 'inference_server' / 'model_template.py'


DEFAULT_INFERENCE_HOST = os.getenv('DEFAULT_INFERENCE_HOST', '0.0.0.0')


@dataclasses.dataclass
class InferenceServer:
    model_file: pathlib.Path
    port: int
    host: str

    def run_inference_server(self, health_check_info: dict | None = None):
        print(
            {
                'PKL_MODEL_PATH': self.model_file,
                'PORT': str(self.port),
                'HOST': self.host,
                'PATH': os.getenv("PATH"),
                **(health_check_info or {})
            }
        )
        return subprocess.Popen(
            ['python', BASE_INFERENCE_TEMPLATE_PATH],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env={
                'PKL_MODEL_PATH': self.model_file,
                'PORT': str(self.port),
                'HOST': self.host,
                'PATH': os.getenv("PATH"),
                **(health_check_info or {})
            }
        )

    @classmethod
    def detect_free_port(cls, host):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        for port in range(1024, 1070):
            try:
                sock.bind((host, port))
                sock.close()
                return port
            except OSError:
                continue

    @classmethod
    def from_generated(cls, model_file):
        host = DEFAULT_INFERENCE_HOST
        port = cls.detect_free_port(host)
        return cls(model_file, port, host)
