# Serverless Notes API — Azure Functions + Cosmos DB + Bicep

A minimal serverless CRUD API deployed entirely from Azure Cloud Shell — no local
admin rights, no VM, no idle-cost risk. Built to demonstrate IaC, managed identity
auth, and monitoring, which is what entry-level Cloud Engineer roles actually screen for.

## Architecture

```
Client
  │
  ▼
Azure Functions (Python, Consumption plan)
  │  (SystemAssigned Managed Identity → RBAC, no keys/connection strings)
  ▼
Cosmos DB (Serverless capacity mode, SQL API)

Application Insights + Log Analytics ← wired to the Function App for tracing/metrics
```

- `POST /api/notes` — create a note, returns generated `id`
- `GET /api/notes/{id}` — retrieve a note by id

## Why these choices (the part interviewers ask about)

- **Consumption plan + Cosmos Serverless**: both bill per-execution/per-request, so
  the whole thing costs pennies for demo traffic and nothing sits idle accruing cost —
  unlike a VM, which bills whether you're using it or not.
- **Managed Identity instead of Cosmos keys**: the Function App's system-assigned
  identity is granted the `Cosmos DB Built-in Data Contributor` role directly on the
  Cosmos account (see `sqlRoleAssignments` in `main.bicep`). The app code never
  touches a secret. **Caveat, stated honestly**: the Functions runtime itself still
  needs a storage account connection string (`AzureWebJobsStorage`) — that's an
  Azure Functions platform requirement, not something managed identity currently
  eliminates. The application-data path (Function → Cosmos) is fully secretless;
  the platform-plumbing path (Function → its own storage) is not. Knowing that
  distinction is itself a good interview answer.
- **Bicep over Terraform**: Bicep is Azure-native — no state file to manage, no
  provider version pinning, deploys with the CLI you already have in Cloud Shell.
  For an Azure-focused role this signals platform depth; Terraform is the better
  choice if you're going multi-cloud later.
- **Application Insights**: wired in at deploy time via `APPLICATIONINSIGHTS_CONNECTION_STRING`,
  so every request is traced from day one — not bolted on after.

## Deploy (from Azure Cloud Shell — takes ~5-10 min)

1. Push this repo to GitHub, then in Cloud Shell:
   ```bash
   git clone <your-repo-url>
   cd azure-serverless-notes
   chmod +x deploy.sh
   ./deploy.sh
   ```
2. That's it — `deploy.sh` creates the resource group, runs `az deployment group create`
   against `main.bicep`, then publishes the function code with `func azure functionapp publish`.

## Manual verification (do this once, take screenshots for your portfolio)

```bash
# Create a note
curl -X POST https://<func-app-name>.azurewebsites.net/api/notes \
  -H "Content-Type: application/json" -d '{"text":"hello world"}'

# Retrieve it
curl https://<func-app-name>.azurewebsites.net/api/notes/<id-from-above>
```

Then go to the Function App → **Application Insights → Live Metrics** in the portal
and watch the request come through. Take a screenshot. Also trigger a deliberate
failure (call `GET /api/notes/not-a-real-id`, confirm you get a 404 and see it in
the traces) — this is your debugging story for interviews.

## Cost

Cosmos DB Serverless + Functions Consumption plan: effectively **$0–1** for demo-level
traffic (Azure free tier also covers a chunk of this on a new subscription).
**Remember to delete the resource group when you're done**: `az group delete --name rg-notes-demo`.

## What I'd change for production

- Partition key is currently just the note's own `id` — fine for a demo, but a real
  workload needs a partition key chosen around actual query/access patterns
  (e.g., a `userId` if notes belong to users) to avoid hot partitions.
- Add API Management in front of the Function for rate limiting, auth (API keys or
  Azure AD), and a stable public surface decoupled from the Function's own URL.
- Move the Function into a VNet-integrated plan with Cosmos private endpoints if this
  needed to be locked down from the public internet.
- Add a GitHub Actions workflow to run `az deployment group create` on push,
  instead of the manual `deploy.sh` — this is the natural "next project."

## Resume bullet

> Designed and deployed a serverless API on Azure (Functions, Cosmos DB, Application
> Insights) using Bicep for infrastructure-as-code; secured data-plane access with
> managed identity and RBAC instead of connection strings.
