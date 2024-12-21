"""
Django migrations package initialization for the protocol service.

This package manages database schema migrations for protocol-related models including:
- Protocol: Research protocol definitions and parameters
- Participation: User enrollment and progress tracking

Migration Features:
- Version-controlled schema management
- Rollback support for failed migrations
- Data integrity preservation during schema changes
- Zero-downtime migration capabilities
- Performance monitoring during migrations

Migration Dependencies:
- services.user.migrations (for User model foreign key relationships)

Database Operations Supported:
- CreateModel: Initial model creation
- AlterField: Field modifications
- AddField: New field additions
- CreateIndex: Index management
- RemoveField: Field removal
- DeleteModel: Model removal

Migration Best Practices:
- Backup verification before migrations
- Staging environment testing
- Production deployment during low-traffic periods
- Data integrity validation post-migration

Version: 1.0.0
"""

# Package initialization - enables Django's migration system
# No additional code required as Django auto-discovers migrations