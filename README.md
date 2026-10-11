# AWS RAG Pipeline

A ready-to-deploy, end-to-end **Retrieval-Augmented Generation (RAG)** template on AWS. Provision everything with Terraform, drop your PDFs into an S3 bucket, and get a working question-answering API over your own documents.

- **Infrastructure as code**: VPC, three subnet tiers, NAT, ALB, ECS Fargate, RDS, S3, IAM and Secrets Manager, all in Terraform
- **Secure network layout**: public ALB in front, the API in private subnets, the database in isolated subnets with no internet route
- **Vector search in Postgres**: RDS PostgreSQL 17 with `pgvector` and an HNSW cosine index
- **Managed AI**: Amazon Bedrock for embeddings (Titan Text Embeddings v2) and answers (Amazon Nova 2 Lite)
- **Simple API**: a FastAPI service with two endpoints, `ingest` and `query`, plus Swagger docs

---

## Architecture

![AWS RAG Pipeline architecture](docs/architecture.png)

> Vector version: [`docs/architecture.svg`](docs/architecture.svg)

### How a request flows

| # | Step |
| --- | --- |
| 1 | The client calls the API through the **Internet Gateway** and the public **Application Load Balancer** (HTTP `:80`). |
| 2 | The ALB forwards to the **Fargate task in a private subnet** on port `8080`. Only the ALB security group is allowed in. |
| 3 | The task stores and searches embeddings in **RDS PostgreSQL + pgvector**, which lives in isolated subnets. |
| 4 | Outbound calls leave through the **NAT Gateway**: image pull, S3 PDFs, Bedrock, Secrets Manager, CloudWatch logs. |
| 5 | One-time: the **Ansible controller** EC2 applies `schema.sql` (pgvector extension, table, HNSW index) to RDS. |

### The RAG logic

- **Ingest** (`POST /api/v1/ingest`): reads PDFs from S3, extracts text page by page, splits it into 1000-character chunks with 200 overlap, embeds each chunk with Titan (1024 dimensions), and stores text, vector and metadata in the `document_chunks` table. Files that are already ingested are skipped.
- **Query** (`POST /api/v1/query`): embeds the question, runs a top-5 cosine similarity search, keeps the best 3 chunks as context, and asks Nova 2 Lite to answer **only** from that context. The response includes the sources (document, chunk, page, similarity).

### What Terraform creates

| File | Resources |
| --- | --- |
| `vpc.tf` | VPC `10.0.0.0/16` with 2 public, 2 private and 2 isolated subnets across 2 AZs |
| `igw-gateway.tf` | Internet Gateway |
| `nat-gateway.tf` | 2 Elastic IPs and 2 NAT Gateways (one per AZ, in the public subnets) |
| `routeTables.tf` | 1 public route table (to IGW), 2 private route tables (to NAT), 2 isolated route tables (no internet route) |
| `alb.tf` | Internet-facing Application Load Balancer (HTTP `:80`), IP target group with `/health` check, security group |
| `ECS.tf` | ECS cluster, Fargate task and service (private subnets, no public IP), IAM roles, Secrets Manager secret, CloudWatch log group, security groups |
| `RDS.tf` | PostgreSQL 17 `db.t3.micro` in the isolated subnets, encrypted, not publicly accessible, 7-day backups |
| `S3Bucket.tf` | Document bucket with versioning, AES256 encryption and public access fully blocked |
| `EC2.tf` / `user_data.sh` | Ansible controller EC2 that installs Ansible, clones this repo and bootstraps the database |

### Network access rules

| Resource | Allowed inbound | Notes |
| --- | --- | --- |
| ALB | TCP `80` from `0.0.0.0/0` | The only public entry point to the API |
| ECS tasks | TCP `8080` from the **ALB security group** only | Private subnets, no public IP |
| RDS | TCP `5432` from the **ECS** and **Ansible** security groups only | Isolated subnets, no internet route |
| Ansible EC2 | TCP `22` from `ssh_cidr` | Defaults to `0.0.0.0/0`, so restrict it |

---

## Prerequisites

- An **AWS account** and an IAM user with an access key and secret key, with permission to create the resources above
- [**Terraform**](https://developer.hashicorp.com/terraform/install) `>= 1.5.0`
- [**AWS CLI**](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html), used to upload your documents
- **Amazon Bedrock model access** in your region for `amazon.titan-embed-text-v2:0` and `global.amazon.nova-2-lite-v1:0`
- An existing **EC2 key pair** in your region. The default name expected is `Default-key-pair`, or set `key_pair_name`
- Your documents as **PDF** files (the ingestion pipeline currently processes `.pdf` only)

---

## Setup: steps to run the whole pipeline

### Step 1: Add your AWS credentials to the provider file

Open [`Terraform/provider.tf`](./Terraform/provider.tf) and fill in your credentials:

```hcl
provider "aws" {
  region     = var.aws_region
  access_key = "YOUR_ACCESS_KEY_ID"
  secret_key = "YOUR_SECRET_ACCESS_KEY"
}
```

> ⚠️ **Never commit real credentials.** Keep this change local, or revert it before pushing. Alternatively, delete the `access_key` and `secret_key` lines and authenticate with `aws configure` or the `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` environment variables. Terraform picks those up automatically.

### Step 2: Add the database password to the tfvars file

Open [`Terraform/terraform.tfvars`](./Terraform/terraform.tfvars) and set the database password:

```hcl
db_username = "postgres"
db_password = "choose-a-strong-password"
```

While you are in this file, also check these values, which are specific to your account and region:

| Variable | What to do |
| --- | --- |
| `bucket_name` | S3 bucket names are **globally unique**. Change `rag-documents-prod-234123` to something of your own |
| `aws_region` / `availability_zones` | Defaults to `ap-south-1`. If you change the region, update the AZs too |
| `ami_id` | Must be an **Amazon Linux 2023** AMI **in your region** (the bootstrap uses `dnf`) |
| `key_pair_name` | Defaults to `Default-key-pair` in `variables.tf`. Must already exist in your account |
| `ssh_cidr` | Recommended: set to `"<your-ip>/32"` |

> ⚠️ Do not commit the password either.

### Step 3: Deploy the infrastructure

```bash
cd Terraform
terraform init
terraform plan
terraform apply
```

Type `yes` when prompted. RDS and the load balancer take several minutes to become ready.

After `apply` finishes, give the stack a few more minutes. The Ansible controller EC2 waits for RDS, then installs the `pgvector` extension and creates the `document_chunks` table. To follow its progress:

```bash
ssh -i <your-key>.pem ec2-user@<ansible_controller_public_ip>
sudo tail -f /var/log/user-data.log
```

When you see `Bootstrap completed successfully`, the database is ready. (`ansible_controller_public_ip` is a Terraform output.)

### Step 4: Open the API docs on the load balancer

The API sits behind the Application Load Balancer. Terraform prints its address as an output:

```bash
terraform output rag_api_alb_dns_name
```

Open this in your browser:

```
http://<ALB-DNS-NAME>/docs
```

You get the interactive Swagger UI with the two APIs:

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/api/v1/ingest` | Read PDFs from S3, embed them and store them in the vector DB |
| `POST` | `/api/v1/query` | Ask a question and get an answer grounded in your documents |

> If you see a `503` error right after deploying, the ECS task is still starting and the ALB has no healthy target yet. Wait a minute or two and refresh. The ALB DNS name stays the same across task restarts.

### Step 5: Add your own files and get your own working RAG model

1. **Upload your PDFs** to the S3 bucket you named in `terraform.tfvars`:

   ```bash
   aws s3 cp ./my-document.pdf s3://<your-bucket-name>/
   # or a whole folder
   aws s3 sync ./my-docs s3://<your-bucket-name>/ --exclude "*" --include "*.pdf"
   ```

2. **Ingest them** by calling `POST /api/v1/ingest` from the Swagger UI (*Try it out → Execute*) or with curl:

   ```bash
   # Ingest every PDF in the bucket (already-ingested files are skipped)
   curl -X POST http://<ALB-DNS-NAME>/api/v1/ingest \
     -H "Content-Type: application/json" \
     -d '{}'

   # Or ingest one specific file
   curl -X POST http://<ALB-DNS-NAME>/api/v1/ingest \
     -H "Content-Type: application/json" \
     -d '{"s3_key": "my-document.pdf", "document_id": "my-document"}'
   ```

3. **Ask questions** with `POST /api/v1/query`:

   ```bash
   curl -X POST http://<ALB-DNS-NAME>/api/v1/query \
     -H "Content-Type: application/json" \
     -d '{"question": "What are the key points in my document?"}'
   ```

   Example response:

   ```json
   {
     "question": "What are the key points in my document?",
     "answer": "…",
     "sources": [
       { "document": "my-document.pdf", "chunk": "chunk-4", "page": 2, "similarity": 0.87 }
     ]
   }
   ```

That is the full pipeline: **upload PDFs → ingest → ask questions.** Repeat step 5 whenever you have new documents.

---

## The container image: Docker Hub, NAT cost and ECR

> **Note:** The current container image, `atharvak2427/rag-app:v1`, is hosted in the author's **public Docker Hub registry**. The Fargate task runs in a private subnet, so pulling it (and reaching S3, Bedrock, Secrets Manager and CloudWatch) goes out through the **NAT Gateways**.
>
> **To save NAT Gateway cost,** you can push the image to **Amazon ECR** and add **VPC endpoints**, so the task reaches AWS services over the AWS network instead of the NAT.

A sketch of that change:

1. **Create an ECR repository** and push your own image. Build for `linux/amd64`, which is what Fargate runs by default, especially if you build on an Apple Silicon Mac:

   ```bash
   docker build --platform linux/amd64 -t <account-id>.dkr.ecr.<region>.amazonaws.com/rag-app:v1 .
   aws ecr get-login-password --region <region> | docker login --username AWS --password-stdin <account-id>.dkr.ecr.<region>.amazonaws.com
   docker push <account-id>.dkr.ecr.<region>.amazonaws.com/rag-app:v1
   ```

2. **Point the task at ECR.** Change the `image` field in `Terraform/ECS.tf` to your ECR image URI. The existing execution role already includes ECR pull permissions.
3. **Add VPC endpoints** for the private subnets, with a security group that allows HTTPS (`443`) from the ECS security group:
   - Gateway endpoint: `s3` (attach it to the private route tables; ECR image layers are served from S3)
   - Interface endpoints: `ecr.api`, `ecr.dkr`, `logs`, `secretsmanager`, `bedrock-runtime`
4. **Remove the NAT route** from the private route tables, and the NAT Gateways and Elastic IPs once everything works without them.

Interface endpoints are billed per hour per AZ, so compare their cost with NAT Gateway cost for your usage before switching.

---

## API reference

### `GET /health`

Health check used by the ALB target group and the ECS container health check. Returns `{"status": "ok", "version": "1.0.0"}`.

### `POST /api/v1/ingest`

| Field | Type | Description |
| --- | --- | --- |
| `s3_key` | string, optional | A single object key to ingest. If omitted, **all PDFs** in the bucket are ingested |
| `document_id` | string, optional | Identifier stored with the chunks. Defaults to the S3 key |

> Ingestion runs synchronously inside the request. Very large documents can take a while because each chunk is embedded one by one, and the server timeout is 120 seconds. For large files, ingest them one at a time.

### `POST /api/v1/query`

| Field | Type | Description |
| --- | --- | --- |
| `question` | string, required | Your question |

Returns the `answer` and a list of `sources` (document, chunk, page, similarity score). If nothing relevant is found, the model replies that it doesn't have enough information in the provided documents.

---

## Configuration

Runtime settings are passed to the container as environment variables. The Bedrock model IDs are set in `Terraform/ECS.tf`; the RAG tuning values are read by the app, with the defaults shown.

| Variable | Value | Where | Meaning |
| --- | --- | --- | --- |
| `BEDROCK_LLM_MODEL` | `global.amazon.nova-2-lite-v1:0` | set in `ECS.tf` | Model used to generate answers |
| `BEDROCK_EMBEDDING_MODEL` | `amazon.titan-embed-text-v2:0` | set in `ECS.tf` | Model used to create embeddings (1024 dimensions) |
| `TOP_K` | `5` | app default | Chunks fetched from the vector DB |
| `RERANK_TOP_K` | `3` | app default | Chunks passed to the LLM |
| `SIMILARITY_THRESHOLD` | `0.75` | app default | Minimum similarity to count a chunk as a strong match |

These model IDs are public identifiers, not secrets. Your own AWS account and the ECS task role are used to call Bedrock, so usage is billed to whoever deploys the stack.

**Changing models**

- **Answer model:** edit `BEDROCK_LLM_MODEL` in `ECS.tf`. The app uses the Bedrock Converse API, so most Bedrock text models work. The model must be available to your account in your region, and the ID must be a valid model or inference-profile ID there.
- **Embedding model:** the code builds Titan-style requests (`inputText`, `dimensions`), so another embedding family needs code changes in `RAG-Ingestion/embedding/embedding.py` and `RAG-Retrieval/embeddings.py`. Update `VECTOR(1024)` in `ansible/sql/schema.sql` to match the new vector size, and re-ingest your documents, because vectors from different models are not comparable.

The chunk size (1000 characters) and overlap (200) are set in `RAG-codebase/RAG-Ingestion/ingestion/chunker.py`.

The ECS service runs `desired_count = 1` task. It is configured across both private subnets, so you can raise the count for more capacity and availability.

### Running the API locally with Docker

```bash
export DB_HOST=<rds-endpoint> DB_USER=postgres DB_PASSWORD=<password>
export AWS_ACCESS_KEY_ID=... AWS_SECRET_ACCESS_KEY=...
export BEDROCK_LLM_MODEL=global.amazon.nova-2-lite-v1:0
docker compose up --build
# API on http://localhost:8081/docs
```

The RDS instance is in an isolated subnet, so for local runs you need your own reachable Postgres with pgvector, or a network path to the VPC.

---

## Project structure

```
.
├── Terraform/               # All AWS infrastructure (VPC, ALB, ECS, RDS, S3, IAM, EC2…)
├── ansible/                 # DB bootstrap: installs pgvector, creates the schema
│   ├── bootstrap.yml
│   ├── postgres_setup.yml
│   └── sql/schema.sql
├── RAG-codebase/
│   ├── RAG-Ingestion/       # S3 → PDF text → chunks → embeddings → pgvector
│   ├── RAG-Retrieval/       # embed question → vector search → prompt → LLM
│   └── api/                 # FastAPI app exposing /ingest, /query, /health
├── docs/                    # Architecture diagram (PNG + SVG)
├── Dockerfile               # Multi-stage image for the API
└── docker-compose.yml       # Local development
```

---

## Security notes

This is a template meant to get you running quickly. Before using it with sensitive data, tighten the following:

- **The API has no authentication by default**, and the ALB listens on plain **HTTP**. The code includes optional Cognito JWT middleware, which activates when `COGNITO_USER_POOL_ID` and `COGNITO_APP_CLIENT_ID` are set (they are not set in `ECS.tf`). For real use, add an HTTPS listener with an ACM certificate and restrict the ALB security group to trusted IPs.
- **Set `HIDE_DOCS=true`** in the task environment to disable `/docs` once you are done testing.
- **Restrict `ssh_cidr`** to your own IP, or remove the Ansible EC2 after setup.
- **Credentials and the DB password** end up in the Terraform state file. Use a remote, encrypted backend for anything beyond experimentation. Add `*.tfstate*`, `.terraform/` and your filled-in `terraform.tfvars` to `.gitignore`, and never commit credentials.
- RDS is set up for development: single-AZ, deletion protection off, no final snapshot.

---

## Cost and cleanup

This stack creates billable resources. The main ones are **two NAT Gateways**, the **Application Load Balancer**, the RDS instance, the Fargate task and Bedrock usage. See [the ECR and VPC endpoint option](#the-container-image-docker-hub-nat-cost-and-ecr) to reduce NAT cost, and destroy the stack when you are not using it.

The S3 bucket is versioned and not force-destroyed, so empty it, including old versions, before destroying:

```bash
aws s3 rm s3://<your-bucket-name> --recursive
# If versions remain, delete them from the S3 console ("Show versions")

cd Terraform
terraform destroy
```
