from enum import Enum


class Permission(str, Enum):
    USERS_READ = "users:read"
    USERS_WRITE = "users:write"

    JOBS_READ = "jobs:read"
    JOBS_WRITE = "jobs:write"

    FRAUD_READ = "fraud:read"
    FRAUD_ANALYZE = "fraud:analyze"

    RECRUITMENT_READ = "recruitment:read"
    RECRUITMENT_WRITE = "recruitment:write"

    AUDIT_READ = "audit:read"

    SYSTEM_ADMIN = "system:admin"