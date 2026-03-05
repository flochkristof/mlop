import logging
import os
import queue
import sys
from typing import Any, Dict, List, Union

logger = logging.getLogger(f"{__name__.split('.')[0]}")
tag = "Settings"


class Settings:
    tag: str = f"{__name__.split('.')[0]}"
    _auth: str = None

    _sys: Dict[str, Any] = None
    dir: str = None
    compat: Dict[str, Any] = None
    project: str = None
    meta: List[str] = None
    message: queue.Queue = None

    mode: str = "perf"  # noop | debug | perf
    disable_store: bool = True  # TODO: make false
    disable_iface: bool = False
    disable_progress: bool = True
    disable_console: bool = False  # disable file-based logging

    _op_name: str = None
    _op_id: int = None
    _op_status: int = -1

    store_db: str = "store.db"
    store_table_num: str = "num"
    store_table_file: str = "file"
    store_max_size: int = 2**14
    store_aggregate_interval: float = 2 ** (-1)

    http_proxy: str = None
    https_proxy: str = None
    insecure_disable_ssl: bool = False

    x_log_level: int = 2**4  # logging.NOTSET
    x_internal_check_process: int = 1  # TODO: make configurable
    x_file_stream_retry_max: int = 2**2
    x_file_stream_retry_wait_min_seconds: float = 2 ** (-1)
    x_file_stream_retry_wait_max_seconds: float = 2
    x_file_stream_timeout_seconds: int = 2**5  # 2**2
    x_file_stream_max_conn: int = 2**5
    x_file_stream_max_size: int = 2**18
    x_file_stream_transmit_interval: int = 2**3
    x_sys_sampling_interval: int = 2**2
    x_sys_label: str = "sys"
    x_grad_label: str = "grad"
    x_param_label: str = "param"

    host: str = None
    url_view: str = None
    url_webhook: str = None

    _url_defaults = {
        "url_app": "https://app.mlop.ai",
        "url_api": "https://api-prod.mlop.ai",
        "url_ingest": "https://ingest-prod.mlop.ai",
        "url_py": "https://py-prod.mlop.ai",
    }
    _url_ports = {"url_app": 3000, "url_api": 3001, "url_ingest": 3003, "url_py": 3004}
    _url_routes = {
        "url_token": ("url_app", "/api-keys"),
        "url_login": ("url_api", "/api/slug"),
        "url_start": ("url_api", "/api/runs/create"),
        "url_stop": ("url_api", "/api/runs/status/update"),
        "url_meta": ("url_api", "/api/runs/logName/add"),
        "url_graph": ("url_api", "/api/runs/modelGraph/create"),
        "url_num": ("url_ingest", "/ingest/metrics"),
        "url_data": ("url_ingest", "/ingest/data"),
        "url_file": ("url_ingest", "/files"),
        "url_message": ("url_ingest", "/ingest/logs"),
        "url_alert": ("url_py", "/api/runs/alert"),
        "url_trigger": ("url_py", "/api/runs/trigger"),
    }

    def __init__(self) -> None:  # mutable defaults
        self._sys = {}
        self.dir = str(os.path.abspath(os.getcwd()))
        self.compat = {}
        self.project = self.tag
        self.meta = []
        self.message = queue.Queue()

    def __getattr__(self, name):
        if name in self._url_routes:
            base_name, route = self._url_routes[name]
            return getattr(self, base_name) + route
        if name in self._url_defaults:
            if self.host is not None:
                return f"http://{self.host}:{self._url_ports[name]}"
            return self._url_defaults[name]
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    def update(self, settings) -> None:
        if isinstance(settings, Settings):
            settings = settings.to_dict()
        for key, value in settings.items():
            setattr(self, key, value)

    def to_dict(self) -> Dict[str, Any]:
        return {key: getattr(self, key) for key in self.__class__.__annotations__}

    def get_dir(self) -> str:
        return os.path.join(
            self.dir,
            "." + self.tag,
            self.project,
            self._op_name,  # str(self._op_id)
        )

    def _nb(self) -> bool:
        return (
            get_console() in ["ipython", "jupyter"]
            or self._nb_colab()
            or self._nb_kaggle()
        )

    def _nb_colab(self) -> bool:
        return "google.colab" in sys.modules

    def _nb_kaggle(self) -> bool:
        return (
            os.getenv("KAGGLE_KERNEL_RUN_TYPE") is not None
            or "kaggle_environments" in sys.modules
            or "kaggle" in sys.modules
        )


def get_console() -> str:
    try:
        from IPython import get_ipython

        ipython = get_ipython()
        if ipython is None:
            return "python"
    except ImportError:
        return "python"

    if "spyder" in sys.modules or "terminal" in ipython.__module__:
        return "ipython"

    connection_file = (
        ipython.config.get("IPKernelApp", {}).get("connection_file", "")
        or ipython.config.get("ColabKernelApp", {}).get("connection_file", "")
    ).lower()
    if "jupyter" not in connection_file:
        return "ipython"
    else:
        return "jupyter"


def setup(settings: Union[Settings, Dict[str, Any], None] = None) -> Settings:
    if isinstance(settings, Settings):
        return settings
    s = Settings()
    if isinstance(settings, dict) and settings:
        s.update(settings)
    return s
