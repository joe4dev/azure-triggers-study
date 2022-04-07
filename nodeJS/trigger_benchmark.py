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


def prepare(spec):
    # Initial custom installation based on custom Pulumi Azure fork: https://github.com/joe4dev/pulumi-azure/commits/37f28ddea54339f672adef7924dd01978dceff10/sdk/nodejs
    # fix_cmd = "cd database && npm install 'https://gitpkg.now.sh/joe4dev/pulumi-azure/sdk/nodejs?37f28ddea54339f672adef7924dd01978dceff10'"
    # spec.run(fix_cmd, image='node12.x')
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
