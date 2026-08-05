# Serverless Notes API

Small CRUD API on Azure. Functions + Cosmos DB, deployed with Bicep from Cloud Shell.

## Endpoints

* `POST /api/notes` - create a note, returns generated id
* `GET /api/notes/{id}` - get a note back by id

## Architecture

```
Client → Azure Function (Python) → Cosmos DB
```

Function auth to Cosmos is via managed identity, no connection string/keys.
App Insights attached for tracing.

## Deploy

```bash
git clone <your-repo-url>
cd azure-serverless-notes
chmod +x deploy.sh
./deploy.sh
```

## Test

```bash
curl -X POST https://<func-app-name>.azurewebsites.net/api/notes \\
  -H "Content-Type: application/json" -d '{"text":"hello world"}'

curl https://<func-app-name>.azurewebsites.net/api/notes/<id-from-above>
```

## Cleanup

```bash
az group delete --name rg-notes-demo
```



\## Screenshots



!\[Application Insights operations](screenshots/app-insights-operations.png)

