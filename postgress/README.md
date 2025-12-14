# PostgreSQL Docker Setup for Distributed Storage

This directory contains the Docker Compose configuration for running PostgreSQL and pgAdmin for the distributed storage system.

## Files

- **docker-compose.yml**: Main Docker Compose configuration
- **.env**: Environment variables (customize as needed)
- **init.sql**: Database initialization script with schema and tables

## Quick Start

### Prerequisites
- Docker
- Docker Compose

### Starting the Services

```bash
docker-compose up -d
```

This will start:
- **PostgreSQL** on `localhost:5432`
- **pgAdmin** on `localhost:5050`

### Stopping the Services

```bash
docker-compose down
```

To remove volumes as well:
```bash
docker-compose down -v
```

## Default Credentials

### PostgreSQL
- **User**: postgres
- **Password**: postgres
- **Database**: distributed_storage
- **Port**: 5432

### pgAdmin
- **Email**: admin@example.com
- **Password**: admin
- **URL**: http://localhost:5050

## Accessing the Database

### Via psql
```bash
psql -h localhost -U postgres -d distributed_storage
```

### Via pgAdmin
1. Open http://localhost:5050
2. Login with the credentials above
3. Add a new server:
   - Host: `postgres`
   - Port: `5432`
   - Username: `postgres`
   - Password: `postgres`

## Database Schema

The initialization script creates the following tables:

- **storage_nodes**: Tracks storage nodes in the distributed system
- **files**: Metadata for stored files
- **file_chunks**: Information about file chunks
- **replicas**: Replication information for chunks
- **transactions**: Transaction logs for operations

## Customizing Configuration

Edit the `.env` file to customize:
- PostgreSQL credentials
- Database name
- Port numbers
- pgAdmin credentials

Then restart the containers:
```bash
docker-compose down
docker-compose up -d
```

## Volumes

- **postgres_data**: Persistent storage for PostgreSQL data

## Network

Services communicate through the `distributed-storage-network` bridge network.

## Troubleshooting

### Check service status
```bash
docker-compose ps
```

### View logs
```bash
docker-compose logs postgres
docker-compose logs pgadmin
```

### Restart services
```bash
docker-compose restart
```
