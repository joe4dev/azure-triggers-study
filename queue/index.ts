import * as appInsights from 'applicationinsights';
import * as azure from '@pulumi/azure';
import * as pulumi from '@pulumi/pulumi';
import * as automation from '@pulumi/pulumi/automation';
import workload from '../workloads/workload';
import * as dotenv from 'dotenv';

dotenv.config({ path: './../.env',});

const handler = async (context : any, queueMessage : any) => {
  // Setup application insights
  appInsights.setup()
    .setAutoDependencyCorrelation(true)
    .setAutoCollectRequests(true)
    .setAutoCollectPerformance(true, true)
    .setAutoCollectExceptions(true)
    .setAutoCollectDependencies(true)
    .setAutoCollectConsole(true)
    .setUseDiskRetryCaching(false)
    .setSendLiveMetrics(false)
    .setDistributedTracingMode(appInsights.DistributedTracingModes.AI_AND_W3C);
  appInsights.defaultClient.setAutoPopulateAzureProperties(true);
  appInsights.start();

  const correlationContext = appInsights.startOperation(context, 'correlationContextQueue');
  appInsights.defaultClient.trackTrace({
    message: 'Custom operationId',
    properties: {
      newOperationId: queueMessage, // queueMessage only consists of operationId
      oldOperationId: correlationContext!.operation.id,
    },
  });
  appInsights.defaultClient.flush();

  return workload();
};

const getStorageResources = async () => {
  // Import shared resources
  const user = await automation.LocalWorkspace.create({})
    .then((ws) => ws.whoAmI()
      .then((i) => i.user));
  const shared = new pulumi.StackReference(`${user}/${process.env.PULUMI_PROJECT_NAME}/shared`);

  const resourceGroupId = shared.requireOutput('resourceGroupId');
  const resourceGroup = azure.core.ResourceGroup.get('ResourceGroup', resourceGroupId);
  const insightsId = shared.requireOutput('insightsId');
  const insights = azure.appinsights.Insights.get('Insights', insightsId);

  new azure.authorization.Assignment("queueBlobDataContributor", {
    scope: resourceGroupId,
    roleDefinitionName: "Storage Queue Data Contributor",
    principalId: process.env.AZURE_PRINCIPAL_ID!,
  })

  const storageAccount = new azure.storage.Account('account', {
    resourceGroupName: resourceGroup.name,
    location: resourceGroup.location,
    accountTier: 'Standard',
    accountKind: 'StorageV2',
    accountReplicationType: 'LRS',
  });

  const queue = new azure.storage.Queue('queue', {
    storageAccountName: storageAccount.name,
  });

  // Queue trigger
  queue.onEvent('QueueTrigger', {
    resourceGroup,
    callback: handler,
    hostSettings: {
      extensions: {
        queues: {
          maxPollingInterval: '00:00:01', // 1s
          batchSize: 32,
          newBatchThreshold: 16,
          visibilityTimeout: "0",
          maxDequeueCount: 5,
        },
      },
    },
    appSettings: {
      APPINSIGHTS_INSTRUMENTATIONKEY: insights.instrumentationKey,
      AZURE_CLIENT_ID: process.env.AZURE_CLIENT_ID,
      AZURE_TENANT_ID: process.env.AZURE_TENANT_ID,
      AZURE_CLIENT_SECRET: process.env.AZURE_CLIENT_SECRET
    },
  });

  return {
    storageAccountName: storageAccount.name,
    queueName: queue.name,
  };
};

module.exports = getStorageResources().then((e) => e);