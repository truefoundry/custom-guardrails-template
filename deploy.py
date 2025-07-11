import logging
from truefoundry.deploy import (
    Build,
    NodeSelector,
    Port,
    LocalSource,
    Resources,
    Service,
    PythonBuild,
)
from truefoundry_sdk import Autoshutdown

logging.basicConfig(level=logging.INFO)

service = Service(
    name="custom-guardrail-server",
    image=Build(
        build_source=LocalSource(local_build=False),
        build_spec=PythonBuild(
            python_version="3.10",
            requirements_path="requirements.txt",
            command="python main.py"
        ),
    ),
    resources=Resources(
        cpu_request=0.5,
        cpu_limit=0.5,
        memory_request=1000,
        memory_limit=1000,
        ephemeral_storage_request=5000,
        ephemeral_storage_limit=10000,
        node=NodeSelector(capacity_type="spot"),
    ),
    ports=[
        Port(
            port=8000,
            protocol="TCP",
            expose=True,
            app_protocol="http",
            host="custom-guardrail-server.<HOST>", # Replace <HOST> with your host name for example: custom-guardrail-server.<your-company-name>.truefoundry.com
        )
    ],
    labels={"tfy_openapi_path": "openapi.json"},
    workspace_fqn="<WORKSPACE_FQN>",
    replicas=1.0,
    auto_shutdown=Autoshutdown(wait_time=900),
)


service.deploy(workspace_fqn="<WORKSPACE_FQN>", wait=False)
