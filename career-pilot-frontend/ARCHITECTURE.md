# Frontend Architecture

```text
src/
├── app/          # routes/providers/app setup
├── pages/        # route-level pages
├── features/     # product features
├── components/   # shared UI
├── services/     # API clients
├── store/        # global client state
├── hooks/        # reusable hooks
├── utils/        # helpers
├── styles/       # global styles/design tokens
└── assets/       # static assets
```

- React Query: server state/caching
- Zustand: small global client state
- React Hook Form + Zod: forms/validation
- Axios: FastAPI client

Keep feature-specific components and hooks inside each feature folder.
