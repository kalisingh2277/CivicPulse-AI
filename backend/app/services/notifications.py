from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.complaint import Complaint
from app.models.notification import Notification


async def create(
    db: AsyncSession,
    user_id: UUID,
    kind: str,
    title: str,
    body: str | None = None,
    issue_id: UUID | None = None,
) -> Notification:
    n = Notification(user_id=user_id, kind=kind, title=title, body=body, issue_id=issue_id)
    db.add(n)
    return n


async def notify_issue_citizens(
    db: AsyncSession, issue_id: UUID, kind: str, title: str, body: str | None = None
) -> int:
    """Notify every citizen who has a complaint attached to this issue. This is how
    the dedup payoff reaches people: fix one issue, all linked reporters hear about it."""
    citizen_ids = (
        await db.execute(
            select(Complaint.citizen_id).where(Complaint.issue_id == issue_id).distinct()
        )
    ).scalars()
    count = 0
    for cid in citizen_ids:
        await create(db, cid, kind, title, body=body, issue_id=issue_id)
        count += 1
    # Day 5 enqueues email fan-out here for each notification.
    return count
