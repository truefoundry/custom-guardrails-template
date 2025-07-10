import logging
from truefoundry.deploy import (
    Build,
    NodeSelector,
    Port,
    LocalSource,
    DockerFileBuild,
    Resources,
    Service,
    PythonBuild,
)

logging.basicConfig(level=logging.INFO)

service = Service(
    name="tfy-guardrail-server",
    image=Build(
        build_source=LocalSource(local_build=False),
        build_spec=PythonBuild(
            python_version="3.10",
            requirements_path="requirements.txt",
            command="python main.py"
        ),
    ),
    resources=Resources(
        cpu_request=0.1,
        cpu_limit=0.1,
        memory_request=200,
        memory_limit=500,
        ephemeral_storage_request=500,
        ephemeral_storage_limit=500,
        node=NodeSelector(capacity_type="spot"),
    ),
    ports=[
        Port(
            port=8000,
            protocol="TCP",
            expose=True,
            app_protocol="http",
            host="test-guardrails-server.tfy-usea1-ctl.devtest.truefoundry.tech",
        )
    ],
    workspace_fqn="tfy-usea1-devtest:mcp",
    replicas=2.0,
)


service.deploy(workspace_fqn="tfy-usea1-devtest:mcp", wait=False)
