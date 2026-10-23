# DataCrossways deployment

This repository contains the Docker Compose deployment for DataCrossways. The
API and frontend remain independent repositories and are cloned into this
directory as ignored build contexts.

## Repository layout

```text
datacrossways/
├── docker-compose.yaml
├── .env
├── secrets/
├── datacrossways_api/
└── ihdh_frontend/
```

## Install

```sh
git clone -b hardenning https://github.com/MaayanLab/datacrossways.git
cd datacrossways
git clone -b hardenning https://github.com/MaayanLab/datacrossways_api.git datacrossways_api
git clone -b hardenning https://github.com/MaayanLab/ihdh_frontend.git ihdh_frontend

cp .env.example .env
mkdir -p secrets
openssl rand -base64 32 > secrets/postgres_password
openssl rand -base64 48 > secrets/flask_secret_key
```

Edit `.env` before deployment. At minimum, set:

- `PUBLIC_BASE_URL` to the externally visible origin.
- `ADMIN_EMAIL` to the initial administrator.
- S3 credentials, region, bucket, and optional compatible-provider endpoint.
- Google OAuth credentials for browser login.

For Google OAuth, register this callback URL:

```text
${PUBLIC_BASE_URL}/api/user/authorize?provider=google
```

## Object storage

AWS S3 needs only `AWS_REGION`, `S3_BUCKET`, and credentials. If credentials are
empty, the AWS SDK credential chain is used, allowing instance and task roles.

For an S3-compatible provider, additionally configure:

```dotenv
S3_ENDPOINT_URL=https://s3.example.org
S3_ADDRESSING_STYLE=path
```

`S3_ADDRESSING_STYLE` accepts `auto`, `path`, or `virtual`. The custom endpoint
must be reachable from the API container, support presigned GET/POST and
multipart operations, and allow browser uploads through its CORS policy.

## Database and startup

### Bundled PostgreSQL

Start the database by enabling its profile:

```sh
docker compose --profile local-db up --build -d
docker compose ps
```

The bundled database reads its password from `DB_PASSWORD_FILE` and persists to
the `postgres_data` volume.

### External PostgreSQL

Set the external connection in `.env`:

```dotenv
DB_HOST=postgres.example.org
DB_PORT=5432
DB_NAME=datacrossways
DB_USER=datacrossways
DB_PASSWORD_FILE=./secrets/postgres_password
DB_SSLMODE=verify-full
```

Then start without the `local-db` profile:

```sh
docker compose up --build -d
docker compose ps
```

The API waits for the external database and runs its idempotent table/bootstrap
initialization before serving requests. `DB_SSLMODE` is passed to both the
startup connection check and SQLAlchemy.

The frontend is the only service published to the host. It serves the SPA and
proxies `/api/` to the API container. PostgreSQL and the API are accessible only
through Compose networks.

Place a TLS load balancer or reverse proxy in front of the configured HTTP port
for production. `PUBLIC_BASE_URL` must use the resulting HTTPS origin.

## Operate

View logs:

```sh
docker compose logs -f
```

Rebuild after updating either nested repository:

```sh
git -C datacrossways_api pull
git -C ihdh_frontend pull
docker compose --profile local-db up --build -d  # omit profile for external DB
```

Stop the deployment without deleting PostgreSQL data:

```sh
docker compose down
```

Deleting the volume is destructive and permanently removes the local metadata
database:

```sh
docker compose down -v
```

Back up the `postgres_data` volume and the configured S3 bucket before upgrades.

## Security notes

- Keep `.env` and `secrets/` out of version control.
- Keep `DEVELOPMENT=false` outside isolated local development.
- Use narrowly scoped AWS credentials or an instance/task role.
- Existing API keys created by versions that stored plaintext keys are not
  accepted. Create replacement keys after upgrading.
- Rotate `flask_secret_key` to invalidate all browser sessions.
