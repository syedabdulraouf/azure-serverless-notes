#!/usr/bin/env bash
# Run this INSIDE Azure Cloud Shell (Bash). No local admin rights needed.
set -euo pipefail

RESOURCE_GROUP="rg-notes-demo"
LOCATION="eastus"   # change if you prefer a closer region

echo "==> Creating resource group..."
az group create --name "$RESOURCE_GROUP" --location "$LOCATION"

echo "==> Deploying infrastructure (Bicep)..."
DEPLOY_OUTPUT=$(az deployment group create \
  --resource-group "$RESOURCE_GROUP" \
  --template-file infra/main.bicep \
  --query properties.outputs -o json)

echo "$DEPLOY_OUTPUT"

FUNC_APP_NAME=$(echo "$DEPLOY_OUTPUT" | python3 -c "import sys, json; print(json.load(sys.stdin)['functionAppName']['value'])")

echo "==> Publishing function code to $FUNC_APP_NAME..."
cd function_app
func azure functionapp publish "$FUNC_APP_NAME" --python
cd ..

echo "==> Done. Test with:"
echo "curl -X POST https://$FUNC_APP_NAME.azurewebsites.net/api/notes -H 'Content-Type: application/json' -d '{\"text\":\"hello world\"}'"
