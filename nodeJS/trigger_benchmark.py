import os
import logging
from dotenv import load_dotenv


BENCHMARK_CONFIG = """
trigger_bench:
  description: Measures the latency to trigger an Azure function.
  provider: azure
  trigger: database
  region: eastus
  runtime: node
"""
supported_triggers = ['http', 'storage', 'queue', 'database', 'serviceBus', 'eventHub', 'eventGrid', 'timer']
DO_INIT = True
# Huge size 2.67GB, see: https://github.com/Azure/azure-functions-docker/issues/323
AZURE_FUNC_IMAGE = 'mcr.microsoft.com/azure-functions/node:3.0-node12-core-tools'
PULUMI_IMAGE = 'pulumi/pulumi:3.28.0'


def prepare(spec):
    # shared = "cd shared/ && npm install"
    # database = "cd database/ && npm install"
    # db_function = "cd database/runtimes/node && npm install && npm run build"
    # It seems that "func extensions install" might not be required given the log output:
    # No action performed. Extension bundle is configured in /Users/joe/Projects/Serverless/azure-triggers-study/nodeJS/database/runtimes/node/host.json.
    # spec.run(db_function, image='node12.x')
    # if DO_INIT:
    #     # Initialization
    #     init = ['shared', spec['trigger'], 'infra']
    #     init_cmd = ' && '.join([f"cd {i} && npm install && cd .." for i in init])
    #     spec.run(init_cmd, image='node12.x')

    # # HACK: Invoke orchestrating deploy script directly. Same for cleanup.
    # # Suggestion 1: Use spec.run() to containerize the invocation
    # # Suggestion 2: Writing a Python orchestrator script is much less error prone than relying on shell scripts
    run_cmd(f"bash deploy.sh -t {spec['trigger']} -l {spec['region']} -r {spec['runtime']}")


def invoke(spec):
    # SHOULD: replace dotenv with SPEC or consider using dotenv as more standardized way of parameter passing in the future instead of custom yml?! Or just for credentials!?
    load_dotenv()
    BENCHMARK_URL = os.getenv('BENCHMARK_URL')
    envs = {
        'BENCHMARK_URL': BENCHMARK_URL
    }
    spec.run_k6(envs)


def cleanup(spec):
    run_cmd(f"bash destroy.sh -t {spec['trigger']}")


def run_cmd(cmd):
    logging.info(cmd)
    os.system(cmd)
