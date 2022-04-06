import os
import logging
from dotenv import load_dotenv


BENCHMARK_CONFIG = """
trigger_bench:
  description: Tests different trigger types.
  provider: azure
  trigger: eventHub
  region: eastus
  runtime: node
"""
supported_triggers = ['http', 'storage', 'queue', 'database', 'serviceBus', 'eventHub', 'eventGrid', 'timer']
DO_INIT = True


def prepare(spec):
    if DO_INIT:
        # Initialization
        init = ['shared', spec['trigger'], 'infra']
        init_cmd = ' && '.join([f"cd {i} && npm install && cd .." for i in init])
        spec.run(init_cmd, image='node12.x')

    # HACK: Invoke orchestrating deploy script directly. Same for cleanup.
    # Suggestion 1: Use spec.run() to containerize the invocation
    # Suggestion 2: Writing a Python orchestrator script is much less error prone than relying on shell scripts
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
