from typing import Generic, TypeVar, Union

import httpx

_AvailableClients = TypeVar(
    '_AvailableClients',
    bound=Union[httpx.AsyncClient, httpx.Client]
)


class BaseClient(Generic[_AvailableClients]):
    _client: _AvailableClients

    @staticmethod
    def base_url(host, port):
        return f"http://{host}:{port}"

    def predict(self, input_data: dict):
        return self._client.post('/api/v2/predict/', json=input_data, timeout=(5, 30))

    def health_check(self):
        return self._client.get('/api/v2/healthcheck', timeout=(5, 30))


class SyncInferenceClient(BaseClient[httpx.Client]):
    def __init__(self, host, port):
        self._client = httpx.Client(base_url=self.base_url(host, port))

