"""Deploy the Lasso Security guardrail wrapper to TrueFoundry as a Service.

Usage:
    pip install -U "truefoundry"
    tfy login
    # Fill in .env (or edit defaults below), then:
    python deploy.py --wait

What this does:
  1. Builds the image from the existing Dockerfile.
  2. Exposes port 8000 on a TrueFoundry-managed HTTPS endpoint.
  3. Wires env vars + secret references for Lasso API access
     and the wrapper's bearer token.
  4. Configures health probes against /health.
"""

import argparse
import os
import subprocess
import sys
import time

from dotenv import load_dotenv
from truefoundry.deploy import (
    Build,
    DockerFileBuild,
    HealthProbe,
    HttpProbe,
    Port,
    Resources,
    Service,
    get_application,
)


def _build_ref() -> str:
    """Short identifier for this deploy. Surfaces as `wrapper_version` on /debug/runtime-config."""
    try:
        sha = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
        dirty = subprocess.call(
            ["git", "diff", "--quiet", "--exit-code"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        return f"{sha}{'-dirty' if dirty else ''}"
    except Exception:
        return f"deploy-{int(time.time())}"


# override=True makes .env the source of truth at deploy time.
load_dotenv(override=True)

# Strip local-dev-only secrets so the SDK uses `tfy login` session auth.
for _runtime_only in ("LASSO_API_KEY", "WRAPPER_API_KEY"):
    os.environ.pop(_runtime_only, None)

# ---------------------------------------------------------------------------
# Placeholders — replace via .env or edit defaults before deploying.
# ---------------------------------------------------------------------------

WORKSPACE_FQN = os.environ.get("TFY_WORKSPACE_FQN", "<workspace>:<name>")
PUBLIC_HOST = os.environ.get("TFY_PUBLIC_HOST", "ml.<cluster>.truefoundry.cloud")
_raw_path = os.environ.get("TFY_PUBLIC_PATH", "").strip()
if _raw_path:
    if not _raw_path.startswith("/"):
        _raw_path = "/" + _raw_path
    if not _raw_path.endswith("/"):
        _raw_path = _raw_path + "/"
PUBLIC_PATH = _raw_path or None

LASSO_API_KEY_SECRET_FQN = os.environ.get(
    "LASSO_API_KEY_SECRET_FQN", "tfy-secret://<workspace>/lasso-guardrails-tfy/lasso-api-key"
)
WRAPPER_API_KEY_SECRET_FQN = os.environ.get(
    "WRAPPER_API_KEY_SECRET_FQN",
    "tfy-secret://<workspace>/lasso-guardrails-tfy/wrapper-api-key",
)

LASSO_API_BASE = os.environ.get("LASSO_API_BASE", "https://server.lasso.security/gateway/v3")

BUILD_REF = _build_ref()


def build_service() -> Service:
    env = {
        "LASSO_API_KEY": LASSO_API_KEY_SECRET_FQN,
        "WRAPPER_API_KEY": WRAPPER_API_KEY_SECRET_FQN,
        "LASSO_API_BASE": LASSO_API_BASE,
        "PORT": "8000",
        "LOG_LEVEL": "info",
        "BUILD_REF": BUILD_REF,
    }
    return Service(
        name="lasso-guardrails-tfy",
        image=Build(build_spec=DockerFileBuild(dockerfile_path="./Dockerfile")),
        ports=[
            Port(
                port=8000,
                host=PUBLIC_HOST,
                **({"path": PUBLIC_PATH} if PUBLIC_PATH else {}),
                protocol="TCP",
                expose=True,
            )
        ],
        env=env,
        resources=Resources(
            cpu_request=0.25,
            cpu_limit=1.0,
            memory_request=512,
            memory_limit=1024,
            ephemeral_storage_request=512,
            ephemeral_storage_limit=1024,
        ),
        liveness_probe=HealthProbe(
            config=HttpProbe(path="/health", port=8000),
            initial_delay_seconds=15,
            period_seconds=30,
            failure_threshold=3,
        ),
        readiness_probe=HealthProbe(
            config=HttpProbe(path="/health", port=8000),
            initial_delay_seconds=5,
            period_seconds=10,
            failure_threshold=3,
        ),
        replicas=1,
    )


def _check_placeholders() -> None:
    fields = {
        "WORKSPACE_FQN": WORKSPACE_FQN,
        "PUBLIC_HOST": PUBLIC_HOST,
        "LASSO_API_KEY_SECRET_FQN": LASSO_API_KEY_SECRET_FQN,
        "WRAPPER_API_KEY_SECRET_FQN": WRAPPER_API_KEY_SECRET_FQN,
    }
    unfilled = [name for name, val in fields.items() if "<" in val or ">" in val]
    if unfilled:
        raise SystemExit(
            "\n".join(
                [
                    "Placeholder values still present in deploy.py for: " + ", ".join(unfilled),
                    "",
                    "Fix via .env or by editing the defaults at the top of deploy.py.",
                    "",
                    "Find cluster-configured host(s) at: Integrations -> Clusters -> <cluster>.",
                    "Find workspace FQN at: Workspaces -> <name> (or `tfy workspace list`).",
                ]
            )
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--wait", action="store_true", help="block until the deploy is healthy")
    args = parser.parse_args()

    _check_placeholders()
    service = build_service()
    service.deploy(workspace_fqn=WORKSPACE_FQN, wait=args.wait)

    if args.wait:
        app_fqn = f"{WORKSPACE_FQN}:lasso-guardrails-tfy"
        app = get_application(app_fqn)
        if app.activeVersion != app.lastVersion:
            print(
                f"\nDEPLOY FAILED: lastVersion={app.lastVersion} but activeVersion={app.activeVersion}.",
                file=sys.stderr,
            )
            print(
                f"The build for v{app.lastVersion} did not reach DEPLOY_SUCCESS; the live pod is still v{app.activeVersion}.",
                file=sys.stderr,
            )
            print(
                f"Check build logs in the TFY dashboard under application id {app.id}.",
                file=sys.stderr,
            )
            sys.exit(1)
        print(f"\nVerified: activeVersion == lastVersion == {app.activeVersion}, build_ref={BUILD_REF}")

    base = f"https://{PUBLIC_HOST}{(PUBLIC_PATH or '').rstrip('/')}"
    print(f"\nDeployed. Endpoints:")
    print(f"  health              : {base}/health")
    print(f"  input validate URL  : {base}/lasso-classify")
    print(f"  output validate URL : {base}/lasso-classify-output")
    print(f"  input mutate URL    : {base}/lasso-classifix")
    print(f"  output mutate URL   : {base}/lasso-classifix-output")
    print(f"  debug               : {base}/debug/runtime-config")
    print(
        "\nNext: register each rail as its own Custom Guardrail Config in the TFY dashboard.\n"
        "Validate rails: Operation = Validate; Mutate rails: Operation = Mutate.\n"
        "Auth = Custom Bearer Auth with wrapper-api-key.\n"
        "With gateway commit a1c551be+, Fail on error: false is the correct default."
    )
