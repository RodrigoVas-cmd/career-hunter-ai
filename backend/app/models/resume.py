from typing import Optional

from sqlalchemy import Boolean, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Resume(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "resumes"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_format: Mapped[str] = mapped_column(String(16), nullable=False)  # pdf | docx
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    raw_text: Mapped[str] = mapped_column(Text, default="", nullable=False)
    extracted_data_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    ambiguities_json: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    parse_status: Mapped[str] = mapped_column(String(32), default="parsed", nullable=False)  # parsed | validated | failed
    is_primary: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class ResumeVersion(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "resume_versions"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    base_resume_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("resumes.id", ondelete="CASCADE"), index=True, nullable=False
    )
    job_posting_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    version_label: Mapped[str] = mapped_column(String(160), nullable=False)
    content_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    changes_summary_json: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    approved_by_user: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    pdf_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    docx_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
