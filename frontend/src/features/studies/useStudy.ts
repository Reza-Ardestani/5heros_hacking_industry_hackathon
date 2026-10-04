import { useEffect, useState } from "react";
import * as studyApi from "./api";
import { defaults } from "./model";
import type { Incidents, IntersectionStudy, Job, Scenario } from "./types";
export function useStudy(go: (step: number) => void) {
  const [scenario, setScenario] = useState<Scenario>(defaults), [incidents, setIncidents] = useState<Incidents | null>(null), [study, setStudy] = useState<IntersectionStudy | null>(null), [job, setJob] = useState<Job | null>(null);
  const [error, setError] = useState(""), [submitting, setSubmitting] = useState(false), [pollError, setPollError] = useState(""), [selected, setSelected] = useState("reference"), [frame, setFrame] = useState(0), [playing, setPlaying] = useState(false), [advanced, setAdvanced] = useState(false);
  const result = job?.result, reference = result?.alternatives[0], recommendation = result?.alternatives.find((a) => a.id === result.recommended_id), active = result?.alternatives.find((a) => a.id === selected);
  const busy = submitting || job?.status === "running", frames = active?.tuning_trial.playback ?? [], current = frames[Math.min(frame, Math.max(0, frames.length - 1))];
  const openStudy = (built: IntersectionStudy) => {
    setStudy(built);
    setScenario(built.scenario);
    go(2);
  };
  const changed = !!result && JSON.stringify(scenario) !== JSON.stringify(result.scenario);
  const averageFlow = (key: "main_vph" | "cross_vph") => scenario.flow_profile
    ? scenario.flow_profile.reduce((total, i) => total + (i.end_s - i.begin_s) * i[key], 0) / scenario.duration_s
    : scenario[key];
  useEffect(() => {
    studyApi.defaults()
      .then((v) => setScenario(v.defaults))
      .catch((e) => setError(e.message));
    studyApi.incidents()
      .then(setIncidents)
      .catch((e) => setError(e.message));
  }, []);
  useEffect(() => {
    if (!job?.id || job.status !== "running")
      return;
    let stopped = false;
    let timer: ReturnType<typeof setTimeout>;
    const poll = async () => {
      try {
        const next = await studyApi.job(job.id);
        if (stopped)
          return;
        setPollError("");
        setJob(next);
        if (next.status === "completed") {
          setSelected(next.result?.recommended_id ?? "reference");
          setFrame(30);
          setPlaying(false);
        }
        if (next.status === "running")
          timer = setTimeout(poll, 900);
      }
      catch (e) {
        if (!stopped) {
          setPollError((e as Error).message);
          timer = setTimeout(poll, 2000);
        }
      }
    };
    timer = setTimeout(poll, 500);
    return () => {
      stopped = true;
      clearTimeout(timer);
    };
  }, [job?.id, job?.status]);
  useEffect(() => {
    if (!playing || !frames.length)
      return;
    const timer = setInterval(() => setFrame((v) => (v + 1) % frames.length), 180);
    return () => clearInterval(timer);
  }, [playing, frames.length]);
  const change = (key: keyof Scenario, value: number) => setScenario((s) => ({ ...s, [key]: value }));
  async function start() {
    if (busy)
      return;
    setError("");
    setPollError("");
    setSubmitting(true);
    setPlaying(false);
    go(3);
    try {
      const next = await studyApi.submit(scenario, study);
      setJob({
        id: next.id,
        status: "running",
        trace: [],
        result: null,
        error: null,
      });
      setSelected("reference");
    }
    catch (e) {
      setError((e as Error).message);
    }
    finally {
      setSubmitting(false);
    }
  }
  async function importProfile(file: File | undefined) {
    if (!file)
      return;
    try {
      const profile = JSON.parse(await file.text());
      if (!Array.isArray(profile.flow_profile) ||
        !profile.flow_profile.length ||
        typeof profile.demand_source !== "string" ||
        !profile.demand_source.trim() ||
        !Number.isInteger(profile.duration_s))
        throw new Error("Use flow_profile, demand_source and duration_s. Format documented in data/README.md.");
      let end = 0;
      for (const i of profile.flow_profile) {
        if (!Number.isInteger(i.begin_s) ||
          !Number.isInteger(i.end_s) ||
          i.begin_s !== end ||
          i.end_s <= i.begin_s ||
          !Number.isFinite(i.main_vph) ||
          !Number.isFinite(i.cross_vph) ||
          i.main_vph < 0 ||
          i.cross_vph < 0)
          throw new Error("Intervals must be contiguous, ordered and contain finite nonnegative arrivals.");
        end = i.end_s;
      }
      if (end !== profile.duration_s)
        throw new Error("Intervals must cover duration_s exactly.");
      setScenario((s) => ({
        ...s,
        demand_kind: "measured",
        flow_profile: profile.flow_profile,
        demand_source: profile.demand_source,
        duration_s: profile.duration_s,
      }));
      setError("");
    }
    catch (e) {
      setError((e as Error).message);
    }
  }
  return { scenario, setScenario, incidents, study, setStudy, job, error, setError, submitting, pollError, selected, setSelected, frame, setFrame, playing, setPlaying, advanced, setAdvanced, result, reference, recommendation, active, busy, frames, current, changed, averageFlow, change, start, importProfile, openStudy };
}
export type StudyController = ReturnType<typeof useStudy>;
