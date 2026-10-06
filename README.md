Vaultline

«A self-hosted household information vault for keeping important information, documents, and expiry dates in one place.»

Vaultline is a lightweight, self-hosted application for organising the information that normally ends up scattered across folders, emails, notes, cloud drives, and paper documents.

Instead of organising everything around folders, Vaultline organises information around entities.

For example:

Car → Insurance → Policy → MOT → Service History → Warranty

The goal is to make important household information easier to find, understand, and maintain without relying on another hosted service.

Why Vaultline?

Household information is often fragmented.

Insurance documents might be in an email. A warranty might be saved somewhere in cloud storage. An MOT date might be written in a note. Important account or ownership information might exist only on paper.

Vaultline was created to provide one place for this information while keeping the data under the user's control.

The project is intentionally self-hosted and designed to run with minimal infrastructure:

- No external SaaS dependency
- No cloud database
- SQLite storage
- Docker deployment
- Simple web interface
- Local document storage
- Searchable household entities
- Expiry dates and important metadata

Vaultline started as a practical project: build something that would actually be useful in a household rather than another generic demo application.

Features

Current V1

- Dashboard
- Household items/entities
- Categories
- Item descriptions and metadata
- Document attachments
- Expiry dates
- Search
- Basic user accounts
- SQLite database
- Docker deployment
- Import/export foundation
- Dark interface
- Persistent local storage

Example use cases

Vaultline can be used for things such as:

- Vehicles
- Insurance policies
- Warranties
- MOT information
- Service records
- Household equipment
- Important documents
- Expiry dates
- Ownership information
- Appliance information
- Property-related records

The entity-based approach means related information can be kept together rather than spread across unrelated folders.

Screenshots

Add screenshots here as the interface develops.

Quick Start

Requirements

- Docker
- Docker Compose
- Linux/macOS/Windows environment capable of running Docker

Clone

git clone https://github.com/KeaganHillery/vaultline.git
cd vaultline

Start Vaultline

docker compose up -d --build

Vaultline will be available on:

http://localhost:8091

If port "8091" is already in use, change the host-side port in "docker-compose.yml".

For example:

ports:
  - "8092:8080"

Initialise persistent storage

The container runs as an unprivileged user. On a fresh installation, make sure the persistent data directory is writable:

sudo chown -R 10001:10001 ./data

Then start the container:

docker compose up -d

Create the first account

Vaultline does not ship with a default username or password.

Create the first account with:

docker exec -it vaultline python -c "from app import db; from werkzeug.security import generate_password_hash; from datetime import datetime; u=input('Username: '); import getpass; p=getpass.getpass('Password: '); c=db(); c.execute('INSERT INTO users(username,password,created_at) VALUES(?,?,?)',(u,generate_password_hash(p),datetime.utcnow().isoformat(timespec='seconds'))); c.commit(); c.close(); print('Account created')"

Then log in through the web interface.

Data & Persistence

Vaultline stores its SQLite database and runtime data in the local "data/" directory.

This directory is intentionally excluded from Git.

Your household data should therefore remain local to your installation.

Back up the data directory regularly:

cp -a data/ ~/vaultline-backup/

For production use, use a proper backup strategy rather than relying on a single copy.

Docker

Check the container:

docker ps

View logs:

docker logs vaultline

Stop Vaultline:

docker compose down

Update the application:

git pull
docker compose up -d --build

Security

Vaultline is currently intended primarily for local/self-hosted use.

V1 should not be exposed directly to the public internet without additional security controls.

Before exposing an installation externally, consider:

- HTTPS
- A reverse proxy
- Strong authentication
- CSRF protection
- Secure session configuration
- Firewall rules
- Encrypted backups
- Access control
- Encrypted storage for sensitive fields

Do not commit ".env" files, databases, uploaded documents, credentials, or other sensitive information to the repository.

Project Structure

vaultline/
├── app.py
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── README.md
├── static/
│   └── style.css
├── templates/
│   ├── base.html
│   ├── dashboard.html
│   ├── item.html
│   ├── item_form.html
│   ├── items.html
│   └── login.html
└── data/
    └── runtime data

Roadmap

Vaultline is still early in development.

Potential future work includes:

- [ ] Improved entity relationships
- [ ] Reminders for expiring items
- [ ] Multi-user permissions
- [ ] Role-based access control
- [ ] Encrypted sensitive fields
- [ ] Secure document handling
- [ ] Better import/export
- [ ] Automated backups
- [ ] Audit history
- [ ] Household sharing
- [ ] Emergency/continuity access
- [ ] Improved mobile interface
- [ ] API
- [ ] More detailed dashboard
- [ ] Notifications

The roadmap is deliberately flexible as the project develops.

Philosophy

Vaultline is built around a few simple principles:

Self-hosted
Your information should not require somebody else's cloud service.

Simple
A household information system should not require a complicated infrastructure stack.

Entity-first
Real-world things have relationships. The software should reflect that.

Portable
Your data should remain accessible and easy to back up.

Practical
Features should solve real problems rather than exist simply because they can be built.

Contributing

Issues, ideas, bug reports, and pull requests are welcome.

If you have an idea for improving Vaultline, open an issue describing the problem and the proposed solution.

License

License information will be added as the project matures.

---

Vaultline — keep your household information organised, searchable, and under your control.
