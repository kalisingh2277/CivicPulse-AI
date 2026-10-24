"""SLA breach scan (docs/02-user-flows.md F6). Admin-triggerable. Flags overdue
open issues as breached.
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def scan_sla(db: AsyncSession) -> int:
    breached = (
        (
            await db.execute(
                text(
                    """
                UPDATE issues SET sla_breached = true
                WHERE sla_breached = false
                  AND status IN ('open','acknowledged','assigned','in_progress','reopened')
                  AND now() > sla_due_at
                RETURNING id
                """
                )
            )
        )
        .mappings()
        .all()
    )
    await db.commit()
    return len(breached)
