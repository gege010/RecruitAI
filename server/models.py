from typing import Literal
from pydantic import BaseModel, Field, model_validator

CRITERIA = ["education", "experience", "skills", "certifications", "languages"]
DEFAULT_WEIGHTS = dict(zip(CRITERIA, [15, 30, 40, 5, 10]))


class JobInput(BaseModel):
    title: str = Field(min_length=3, max_length=120)
    department: str = Field(default="Engineering", max_length=80)
    location: str = Field(default="Jakarta · Hybrid", max_length=120)
    description: str = Field(default="", max_length=8000)
    required_skills: list[str] = Field(min_length=1, max_length=40)
    required_experience_months: int = Field(default=36, ge=0, le=480)
    required_education_level: Literal["", "SMA", "D3", "S1", "S2", "S3"] = "S1"
    required_certifications: list[str] = Field(default_factory=list, max_length=20)
    required_languages: list[str] = Field(
        default_factory=lambda: ["Indonesia"], max_length=15
    )
    weights: dict[str, float] = Field(default_factory=lambda: DEFAULT_WEIGHTS.copy())

    @model_validator(mode="after")
    def validate_content(self):
        self.title = self.title.strip()
        if len(self.title) < 3:
            raise ValueError("Nama posisi minimal 3 karakter.")
        unique = {}
        for skill in self.required_skills:
            if skill.strip():
                unique.setdefault(skill.strip().casefold(), skill.strip())
        self.required_skills = list(unique.values())
        if not self.required_skills or any(len(s) > 100 for s in self.required_skills):
            raise ValueError(
                "Isi setidaknya satu keahlian, maksimal 100 karakter per keahlian."
            )
        if set(self.weights) != set(CRITERIA):
            raise ValueError("Kelima bobot kriteria wajib diisi.")
        import math

        if (
            any(not math.isfinite(v) or v < 0 for v in self.weights.values())
            or sum(self.weights.values()) <= 0
        ):
            raise ValueError(
                "Bobot harus bernilai positif atau nol dengan total lebih dari nol."
            )
        total = sum(self.weights.values())
        self.weights = {k: round(self.weights[k] / total * 100, 6) for k in CRITERIA}
        return self


class ProfileInput(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    headline: str = Field(default="", max_length=160)
    skills: list[str] = Field(default_factory=list, max_length=100)
    experience_months: int | None = Field(default=None, ge=0, le=600)
    education: Literal["", "SMA", "D3", "S1", "S2", "S3"] = ""
    certifications: list[str] = Field(default_factory=list, max_length=40)
    languages: list[str] = Field(default_factory=list, max_length=20)
    summary: str = Field(default="", max_length=4000)


class ReviewInput(BaseModel):
    status: Literal["new", "shortlisted", "hold", "rejected"]
    note: str = Field(default="", max_length=2000)
    version: int = Field(ge=1)


class JobUpdate(JobInput):
    version: int = Field(ge=1)


class LoginInput(BaseModel):
    password: str = Field(max_length=256)
