# Vaultline V1

A self-hosted household information vault.

## Run

```bash
docker compose up -d --build
```

Open `http://SERVER-IP:8090`.

V1 creates no default account. Create the first account with:

```bash
docker exec -it vaultline python -c "from app import db; from werkzeug.security import generate_password_hash; from datetime import datetime; import getpass; u=input('Username: '); p=getpass.getpass('Password: '); c=db(); c.execute('INSERT INTO users(username,password,created_at) VALUES(?,?,?)',(u,generate_password_hash(p),datetime.utcnow().isoformat(timespec='seconds'))); c.commit(); c.close(); print('Account created')"
```

## V1 features

- Local SQLite database
- Login
- Household items/entities
- Categories
- Search
- Expiry/renewal dates
- Document uploads
- Document downloads/deletion
- Audit log
- JSON export
- Docker deployment
- No external services

Do not expose this directly to the public internet yet. Put it behind your existing private network/Tailscale/reverse proxy until HTTPS, CSRF protection, stronger authentication and encrypted-at-rest design are added.
