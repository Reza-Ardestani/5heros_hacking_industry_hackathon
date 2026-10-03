"""HTTP-independent scenario and intervention contracts."""

from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class FlowInterval(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    begin_s: int = Field(ge=0, le=1800)
    end_s: int = Field(gt=0, le=1800)
    main_vph: float = Field(ge=0, le=1800)
    cross_vph: float = Field(ge=0, le=600)


class Scenario(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    main_vph: float = Field(default=1050, ge=50, le=1800)
    cross_vph: float = Field(default=160, ge=20, le=600)
    duration_s: int = Field(default=900, ge=300, le=1800)
    seed: int = Field(default=42, ge=0, le=100000)
    budget_cad: float = Field(default=100000, ge=0, le=10000000)
    cross_guardrail_pct: float = Field(default=30, ge=0, le=200)
    retiming_cost_cad: float = Field(default=15000, ge=0, le=1000000)
    widening_cost_cad: float = Field(default=1200000, ge=0, le=10000000)
    annual_operating_cost_cad: float = Field(default=2000, ge=0, le=1000000)
    occupancy: float = Field(default=1.2, ge=1, le=6)
    value_of_time_cad: float = Field(default=20, ge=0, le=200)
    operating_days: int = Field(default=250, ge=1, le=365)
    asset_life_years: int = Field(default=10, ge=1, le=50)
    demand_kind: Literal["synthetic", "measured"] = "synthetic"
    demand_source: str = Field(
        default="Synthetic directional arrivals; not CalTRACS", max_length=500
    )
    flow_profile: list[FlowInterval] | None = Field(default=None, max_length=12)

    @model_validator(mode="after")
    def validate_profile(self):
        if self.demand_kind == "measured" and (
            not self.flow_profile or not self.demand_source.strip()
        ):
            raise ValueError("Measured arrivals require a flow profile and source/study citation")
        if self.flow_profile is not None:
            if not self.flow_profile:
                raise ValueError("Flow profile cannot be empty")
            end = 0
            for interval in self.flow_profile:
                if interval.begin_s != end or interval.end_s <= interval.begin_s:
                    raise ValueError("Flow intervals must be contiguous, ordered and start at zero")
                end = interval.end_s
            if end != self.duration_s:
                raise ValueError("Flow profile must cover duration_s exactly")
            if all(i.main_vph == 0 and i.cross_vph == 0 for i in self.flow_profile):
                raise ValueError("Flow profile must contain traffic")
        return self

    def intervals(self) -> list[FlowInterval]:
        return self.flow_profile or [
            FlowInterval(
                begin_s=0,
                end_s=self.duration_s,
                main_vph=self.main_vph,
                cross_vph=self.cross_vph,
            )
        ]

    def average_flows(self) -> tuple[float, float]:
        return tuple(
            sum((i.end_s - i.begin_s) * getattr(i, key) for i in self.intervals()) / self.duration_s
            for key in ("main_vph", "cross_vph")
        )


@dataclass(frozen=True)
class Intervention:
    id: str
    label: str
    main_green_share: float
    main_lanes: int
    capital_cost_cad: float


def bounded_share(share: float) -> float:
    return round(max(0.30, min(0.80, share)), 3)
