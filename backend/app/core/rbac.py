from app.core.permissions import Permission

ROLE_PERMISSIONS = {
    "admin": {
        Permission.SYSTEM_ADMIN,
        Permission.USERS_READ,
        Permission.USERS_WRITE,
        Permission.AUDIT_READ,
        Permission.JOBS_READ,
        Permission.JOBS_WRITE,
        Permission.FRAUD_READ,
        Permission.FRAUD_ANALYZE,
        Permission.RECRUITMENT_READ,
        Permission.RECRUITMENT_WRITE,
    },

    "analyst": {
        Permission.FRAUD_READ,
        Permission.FRAUD_ANALYZE,
    },

    "recruiter": {
        Permission.RECRUITMENT_READ,
        Permission.RECRUITMENT_WRITE,
        Permission.JOBS_READ,
        Permission.JOBS_WRITE,
    },

    "viewer": {
        Permission.JOBS_READ,
        Permission.RECRUITMENT_READ,
        Permission.FRAUD_READ,
    },
}