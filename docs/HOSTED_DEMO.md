# Free hosted demo

The Render Blueprint runs the React build and the FastAPI API in one free web service, so browser sign-in stays on the same origin. A separate Neon Free Postgres project keeps database storage independent of the web container. Use a direct database URL with TLS because the live views use PostgreSQL LISTEN notifications.

1. In Neon, create an isolated Free project with PostgreSQL 18 and choose its direct connection string by turning connection pooling off on the Connect panel.
2. Connect the repository in Render and apply the root Blueprint. It specifies the Free plan. Provide the database connection string as the private `DATABASE_URL` environment variable. Render generates `SECRET_KEY`.
3. Wait for the `/health` readiness probe. The service migrates the database and loads fictional sample data. Create a new customer account on the hosted sign-in page to explore the app. Seeded staff credentials are randomly generated and visible to the account owner in the first startup log.

The web service sleeps when idle. The optional periodic maintenance worker runs under the local Compose `automation` profile. A free hosted web service does not guarantee that jobs run while it sleeps.

[Render Free plan](https://render.com/docs/free) · [Neon Free plan](https://neon.com/blog/neon-free-plan-1-gb-per-project)

The hosted seed adds 360 synthetic completed sessions over the preceding 90 days. For a local seeded demo, run `python -m database.seed.history --confirm-demo-database` to load the same dataset. Rerunning does not duplicate the batch.
