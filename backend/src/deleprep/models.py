from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, JSON
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    progress = relationship("UserProgress", back_populates="user")
    submissions = relationship("TaskSubmission", back_populates="user")

class SkillTag(Base):
    __tablename__ = "skill_tags"
    id = Column(String, primary_key=True, index=True)
    name = Column(String)
    category = Column(String)
    parent_id = Column(String, ForeignKey("skill_tags.id"), nullable=True)
    children = relationship("SkillTag", back_populates="parent")
    parent = relationship("SkillTag", back_populates="children", remote_side=[id])

class UserProgress(Base):
    __tablename__ = "user_progress"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    skill_tag_id = Column(String, ForeignKey("skill_tags.id"))
    mastery_score = Column(Float, default=0.0)
    user = relationship("User", back_populates="progress")
    skill_tag = relationship("SkillTag")

class TaskSubmission(Base):
    __tablename__ = "task_submissions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    task_type = Column(String)
    scenario = Column(String)
    bullet_points = Column(JSON)
    target_skills = Column(JSON)
    submission_text = Column(String, nullable=True)
    score = Column(Integer, nullable=True)
    verdict = Column(String, nullable=True)
    succeeded_tags = Column(JSON, nullable=True)
    failed_tags = Column(JSON, nullable=True)
    overall_feedback = Column(String, nullable=True)
    user = relationship("User", back_populates="submissions")
    corrections = relationship("Correction", back_populates="submission")

class Correction(Base):
    __tablename__ = "corrections"
    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("task_submissions.id"))
    original = Column(String)
    correction = Column(String)
    explanation = Column(String)
    submission = relationship("TaskSubmission", back_populates="corrections")
