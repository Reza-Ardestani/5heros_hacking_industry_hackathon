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


ExtraOption = Literal["signal_control", "incident_clearance", "turn_lane", "turn_ban"]


class IncidentSpec(BaseModel):
    """A lane-blocking incident at the hotspot junction (J2), modeled as stopped vehicles."""

    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    direction: Literal["east", "west"] = "east"
    start_s: int = Field(default=300, ge=0, le=1800)
    duration_s: int = Field(default=1200, ge=60, le=3600)
    lanes_blocked: int = Field(default=1, ge=1, le=3)
    label: str = Field(default="Lane-blocking incident (assumed)", max_length=200)


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
    # Sprint 2-3 study features. Defaults reproduce the original four-option study.
    arterial_lanes: int = Field(default=1, ge=1, le=3)
    junction_control: Literal["signal", "priority"] = "signal"
    turn_share: float = Field(default=0, ge=0, le=0.4)
    incident: IncidentSpec | None = None
    extra_options: list[ExtraOption] = Field(default_factory=list, max_length=4)
    clearance_reduction: float = Field(default=0.5, ge=0.1, le=0.9)
    # Share of study windows an incident is active (from six months of City data for an
    # intersection study); 1 = evaluate incident conditions only.
    incident_weight: float = Field(default=1.0, ge=0, le=1)
    signal_install_cost_cad: float = Field(default=250000, ge=0, le=10000000)
    signal_removal_cost_cad: float = Field(default=30000, ge=0, le=10000000)
    clearance_program_cost_cad: float = Field(default=50000, ge=0, le=10000000)
    turn_lane_cost_cad: float = Field(default=400000, ge=0, le=10000000)
    turn_ban_cost_cad: float = Field(default=10000, ge=0, le=10000000)

    @model_validator(mode="after")
    def validate_profile(self):
        if self.incident and self.incident.lanes_blocked > self.arterial_lanes:
            raise ValueError("Incident cannot block more lanes than the arterial has")
        if {"turn_lane", "turn_ban"} & set(self.extra_options) and self.turn_share == 0:
            raise ValueError("Turn lane/ban options need a left-turn share above zero")
        if "incident_clearance" in self.extra_options and not self.incident:
            raise ValueError("Faster incident clearance needs an incident to clear")
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
    # Hotspot junction (J2) changes; defaults keep the original corridor.
    control: Literal["signal", "priority"] | None = None  # None = scenario's junction_control
    incident_duration_factor: float = 1.0
    turn_lane: bool = False
    turn_ban: bool = False
    kind: str = "retiming"


def bounded_share(share: float) -> float:
    return round(max(0.30, min(0.80, share)), 3)
