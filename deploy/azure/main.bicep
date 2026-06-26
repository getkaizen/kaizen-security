// Kaizen Sandbox for Azure, Bicep module.
// Deploys the in-tenant detector as an Azure Container App (the same image as AWS) next to
// your agent. It watches the agent's reasoning trace and real egress, decides with your own
// model key, and sends out only the verdict.

@description('Your Kaizen API key (kz_live_...). The verdict destination.')
@secure()
param kaizenApiKey string

@description('The agent name verdicts are recorded under.')
param agentName string = 'agent'

@description('OpenAI key for the reasoning (Azure path uses OpenAI for now).')
@secure()
param openaiApiKey string

param image string = 'ghcr.io/getkaizen/kaizen-sandbox:latest'
param location string = resourceGroup().location
param kaizenApiUrl string = 'https://api.getkaizen.io'

resource env 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: 'kaizen-sandbox-env'
  location: location
  properties: {}
}

resource app 'Microsoft.App/containerApps@2024-03-01' = {
  name: 'kaizen-sandbox'
  location: location
  properties: {
    managedEnvironmentId: env.id
    configuration: {
      ingress: { external: false, targetPort: 8081, additionalPortMappings: [ { targetPort: 8080 } ] }
      secrets: [
        { name: 'kaizen-key', value: kaizenApiKey }
        { name: 'openai-key', value: openaiApiKey }
      ]
    }
    template: {
      containers: [
        {
          name: 'kaizen-sandbox'
          image: image
          resources: { cpu: json('0.5'), memory: '1Gi' }
          env: [
            { name: 'KZ_AGENT', value: agentName }
            { name: 'KZ_MODEL_BACKEND', value: 'openai' }
            { name: 'KAIZEN_API_URL', value: kaizenApiUrl }
            { name: 'KAIZEN_API_KEY', secretRef: 'kaizen-key' }
            { name: 'OPENAI_API_KEY', secretRef: 'openai-key' }
          ]
        }
      ]
      scale: { minReplicas: 1, maxReplicas: 1 }
    }
  }
}
