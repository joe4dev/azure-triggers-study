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
# Huge size 2.67GB, see: https://github.com/Azure/azure-functions-docker/issues/323
AZURE_FUNC_IMAGE = 'mcr.microsoft.com/azure-functions/node:3.0-node12-core-tools'
PULUMI_IMAGE = 'pulumi/pulumi:3.28.0'

DO_INIT = True


def prepare(spec):
    if DO_INIT:
        init = ['shared', spec['trigger'], 'infra']
        init_cmd = ' && '.join([f"cd {i} && npm install && cd .." for i in init])
        spec.run(init_cmd, image='node12.x')
        if spec['trigger'] == 'database':
            db_init_cmd = 'cd database/runtimes/node && npm install && npm run build'
            spec.run(db_init_cmd, image='node12.x')

    run_cmd(f"bash deploy.sh -t {spec['trigger']} -l {spec['region']} -r {spec['runtime']}")


def invoke(spec):
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
