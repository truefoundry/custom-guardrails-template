import logging
from truefoundry.deploy import (
    Service,
    NodeSelector,
    PythonBuild,
    LocalSource,
    Build,
    Port,
    Autoshutdown,
    Resources,
)

logging.basicConfig(level=logging.INFO)

service = Service(
    name="custom-guardrail-server",
    image=Build(
        build_source=LocalSource(local_build=False),
        build_spec=PythonBuild(
            python_version="3.10",
            build_context_path="./",
            requirements_path="requirements.txt",
            command="python main.py",
        ),
    ),
    resources=Resources(
        cpu_request=0.5,
        cpu_limit=0.5,
        memory_request=1000,
        memory_limit=1000,
        ephemeral_storage_request=20000,
        ephemeral_storage_limit=50000,
        node=NodeSelector(capacity_type="spot"),
    ),
    ports=[
        Port(
            port=8000,
            protocol="TCP",
            expose=True,
            app_protocol="http",
            host="custom-guardrail-server.tfy-usea1-ctl.devtest.truefoundry.tech",
        )
    ],
    labels={"tfy_openapi_path": "openapi.json"},
    workspace_fqn="tfy-usea1-devtest:hrithik-t-1",
    replicas=1.0,
    auto_shutdown=Autoshutdown(wait_time=10000),
)


service.deploy(workspace_fqn="tfy-usea1-devtest:hrithik-t-1", wait=False)
