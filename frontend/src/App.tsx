import { ChevronRight, FileText, FlaskConical, GitBranch, Info, Route, Settings2, TrafficCone, X } from "lucide-react";
import { useState } from "react";
import { ChatDock } from "./features/assistant";
import { IntersectionExplorer, getIntersectionStudy } from "./features/intersections";
import { ReportLink, StudiesWorkspace, StudyProgress, useStudy } from "./features/studies";
import type { ChatAction, ExplorerCommand, View } from "./shared/navigation";
export default function App() {
  const [view, setView] = useState<View>("problem");
  const [step, setStep] = useState(1);
  const [command, setCommand] = useState<ExplorerCommand | null>(null);
  const go = (next: number) => { setStep(next); setView(next === 1 ? "problem" : next === 4 ? "compare" : "study"); window.scrollTo({ top: 0, behavior: "smooth" }); };
  const controller = useStudy(go);
  const { result, error, setError, changed, openStudy } = controller;
  const exportLink = <ReportLink controller={controller} />;
  const runChatAction = async (a: ChatAction) => {
    if (a.type === "study") {
      openStudy(await getIntersectionStudy(a.intersection));
      return;
    }
    const { type: _type, view: target, step: next, ...rest } = a;
    if (target === "intersections") {
      setView("intersections");
      setCommand({ ...rest, nonce: Date.now() });
    }
    else if (target === "evidence")
      setView("evidence");
    else
      go(next ?? (target === "problem" ? 1 : target === "compare" ? 4 : 2));
  };
  return (<div className="app-shell">
    <aside className="sidebar">
      <a className="brand" href="#" onClick={(e) => {
        e.preventDefault();
        go(1);
      }}>
        <span className="brand-icon">
          <Route size={22} />
        </span>
        <span>
          Bottleneck
          <br />
          <strong>Busters</strong>
        </span>
      </a>
      <div className="sidebar-caption">PLANNING WORKSPACE</div>
      <nav>
        {([
          ["problem", FlaskConical, "Guided study", "01"],
          ["compare", GitBranch, "Compare options", "02"],
          ["intersections", TrafficCone, "Intersections", "03"],
          ["evidence", FileText, "Evidence & sources", "04"],
        ] as const).map(([id, Icon, label, index]) => (<button className={view === id || (id === "problem" && view === "study")
          ? "selected"
          : ""} aria-label={label} onClick={() => id === "problem"
            ? go(1)
            : id === "compare"
              ? go(4)
              : setView(id)} key={id}>
          <Icon size={18} />
          <span>{label}</span>
          <small>{index}</small>
        </button>))}
      </nav>
      <div className="sidebar-bottom">
        <span className="status-dot" /> Local prototype
        <div>Calgary · Hackathon 2026</div>
        <p>Plan. Test. Revise.</p>
      </div>
    </aside>
    <main>
      <header className="topbar">
        <div className="breadcrumbs">
          Workspace <ChevronRight size={14} />{" "}
          <strong>
            {view === "evidence"
              ? "Evidence & sources"
              : view === "intersections"
                ? "Intersection explorer"
                : `Step ${step} of 4`}
          </strong>
        </div>
        <div className="topbar-meta">
          <span className="badge neutral">STUDY 001</span>
          <span className="avatar">BB</span>
        </div>
      </header>
      <div className="page-body">
        <StudyProgress controller={controller} view={view} step={step} go={go} />
        <section className="page-heading">
          <div>
            <div className="eyebrow">CALGARY / TRANSPORTATION PLANNING</div>
            <h1>
              {view === "problem"
                ? "Which change earns its cost?"
                : view === "study"
                  ? step === 2
                    ? "Define the changes worth testing."
                    : "Let the evidence decide."
                  : view === "compare"
                    ? "A recommendation you can inspect."
                    : view === "intersections"
                      ? "Where does traffic keep getting stuck?"
                      : "Show your working."}
            </h1>
            <p>
              {view === "problem"
                ? "A guided corridor study for better traffic flow, within budget constraints."
                : view === "study"
                  ? step === 2
                    ? "Set demand, spending limits and the cross-street protection rule."
                    : "Watch agents test, reject, revise and evaluate traffic interventions."
                  : view === "compare"
                    ? "Compare the whole corridor, the tradeoffs and the investment required."
                    : view === "intersections"
                      ? "Six months of City-reported incidents and closures by intersection, with the live City feed and cameras. Use it to choose which corridor to study."
                      : "Trace each decision back to inputs, assumptions and actual simulator output."}
            </p>
          </div>
          <div className="heading-actions">
            {result && exportLink}
            {view === "evidence" && (<button className="button primary" onClick={() => go(2)}>
              <Settings2 size={16} />
              Edit study
            </button>)}
          </div>
        </section>
        {error && (<div className="notice error" role="alert">
          <Info size={18} />
          <span>{error}</span>
          <button aria-label="Dismiss error" onClick={() => setError("")}>
            <X size={16} />
          </button>
        </div>)}
        {changed && (<div className="notice warning">
          <Info size={17} />
          <span>
            Inputs changed. Results still describe the previous run. Run
            again to update the comparison.
          </span>
        </div>)}
        {view === "intersections" && (<IntersectionExplorer onStudy={openStudy} command={command} />)}
        <StudiesWorkspace controller={controller} view={view} step={step} go={go} onEvidence={() => setView("evidence")} />




        <footer>
          <span>
            BOTTLENECK BUSTERS{" "}
            <span> / Planning evidence, before investment.</span>
          </span>
          <span>Local study · v0.1</span>
        </footer>
      </div>
    </main>
    <ChatDock onAction={runChatAction} />
  </div>);
}
