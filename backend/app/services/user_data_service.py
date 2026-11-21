from typing import Iterable, Optional

from ..extensions import db
from ..models import Developer, UserDeveloper


def link_developer_to_user(user_id: Optional[int], developer_id: Optional[int], source: str = "manual") -> bool:
    if not user_id or not developer_id:
        return False
    exists = UserDeveloper.query.filter_by(user_id=user_id, developer_id=developer_id).first()
    if exists:
        return False
    db.session.add(UserDeveloper(user_id=user_id, developer_id=developer_id, source=source or "manual"))
    return True


def link_developers_to_user(user_id: Optional[int], developer_ids: Iterable[int], source: str = "manual") -> None:
    for developer_id in developer_ids:
        link_developer_to_user(user_id, developer_id, source=source)


def user_developer_query(user_id: Optional[int]):
    query = Developer.query
    if not user_id:
        return query.filter(False)
    return query.join(UserDeveloper, UserDeveloper.developer_id == Developer.id).filter(UserDeveloper.user_id == user_id)


def user_can_access_developer(user_id: Optional[int], developer_id: int) -> bool:
    if not user_id:
        return False
    return (
        UserDeveloper.query.filter_by(user_id=user_id, developer_id=developer_id).first()
        is not None
    )
