import * as azure from '@pulumi/azure'
import * as cosmosdb from '@pulumi/azure/cosmosdb'
import * as automation from '@pulumi/pulumi/automation'
import * as pulumi from '@pulumi/pulumi'
import * as dotenv from 'dotenv'
import handler from './handler'

dotenv.config({ path: './../.env' })

const getDatabaseResources = async () => {
  // Import shared resources
  const user = await automation.LocalWorkspace.create({}).then(ws =>
    ws.whoAmI().then(i => i.user)
  )
  const shared = new pulumi.StackReference(
    `${user}/${process.env.PULUMI_PROJECT_NAME}/shared`
  )

  const insightsId = shared.requireOutput('insightsId')
  const insights = azure.appinsights.Insights.get('Insights', insightsId)

  const sqlAccount = cosmosdb.Account.get(
    process.env.ACCOUNTDB_NAME!,
    process.env.ACCOUNTDB_ID!
  )

  const sqlDatabase = cosmosdb.SqlDatabase.get(
    process.env.DATABASE_NAME!,
    process.env.DATABASE_ID!
  )

  const sqlContainer = cosmosdb.SqlContainer.get(
    process.env.CONTAINER_NAME!,
    process.env.CONTAINER_ID!
  )

  const connectionKey = `Cosmos${process.env['ACCOUNTDB_NAME']}ConnectionKey`

  // SQL on change trigger
  const sqlEvent = sqlAccount.onChange('databaseTrigger', {
    databaseName: sqlDatabase.name,
    collectionName: sqlContainer.name,
    startFromBeginning: true,
    location: process.env.PULUMI_AZURE_LOCATION,
    callback: handler,
    appSettings: {
      APPINSIGHTS_INSTRUMENTATIONKEY: insights.instrumentationKey,
      [connectionKey]: `AccountEndpoint=${process.env.ACCOUNTDB_ENDPOINT};AccountKey=${process.env.ACCOUNTDB_PRIMARYKEY};`
    }
  })

  return {
    databaseName: sqlDatabase.name,
    containerName: sqlContainer.name,
    functionApp: sqlEvent.functionApp.endpoint.apply(e =>
      e.replace('/api/', '')
    )
  }
}

module.exports = getDatabaseResources().then(e => e)