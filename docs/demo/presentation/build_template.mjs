import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { Presentation, PresentationFile } from '@oai/artifact-tool';

const repo=process.env.BB_REPO ?? '/Users/reza/Documents/GitHub/5heros_hacking_industry_hackathon';
const skill='/Users/reza/.codex/plugins/cache/openai-primary-runtime/presentations/26.905.11957/skills/presentations';
const python='/Users/reza/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3';
const work=path.join(repo,'output/presentation');
const build=path.join(work,'.build');
const {resolvePresentationFont,applyPresentationChartFont,finalizePresentation}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')).href);
const font=resolvePresentationFont({fontFamily:'Liberation Sans'});
const tokens=JSON.parse(await fs.readFile(path.join(repo,'frontend/src/design-tokens/tokens.json'),'utf8'));
const c=tokens.color;
const p=Presentation.create({slideSize:{width:1280,height:720}});
const sources={rubric:'organizer_docs/JUDGING_RUBRIC.md',data:'data/analysis/README.md',design:'docs/design/disruption-data/design.md',updates:'organizer_docs/discord/updates-2026-10-03-evening.md'};

function text(s,value,x,y,w,h,size=28,color=c.ink,bold=false){
 const sh=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
 sh.text=value;sh.text.style={typeface:font,fontSize:size,bold,color,autoFit:'none'};return sh;
}
function rect(s,x,y,w,h,fill,line='none'){return s.shapes.add({geometry:'rect',position:{left:x,top:y,width:w,height:h},fill,line:{fill:line,width:line==='none'?0:1}});}
function slide(title,n,dark=false){const s=p.slides.add();s.background.fill=dark?c.nav:c.surface;
 text(s,title,68,52,1144,110,46,dark?c.surface:c.nav,true);
 text(s,'Bottleneck Busters',68,661,1020,30,18,dark?c.navText:c.muted);
 text(s,String(n).padStart(2,'0'),1160,661,52,30,18,dark?c.navText:c.muted);return s;
}
function notes(s,t,src=[]){s.speakerNotes.textFrame.setText(t+'\n\nSources:\n'+src.join('\n'));}
function table(s,values,x,y,width,height,colWidths){
 const t=s.tables.add({rows:values.length,columns:values[0].length,left:x,top:y,width,height,values,columnWidths:colWidths});
 t.borders.assign({fill:c.border,width:1,style:'solid'});
 t.cells.block({row:0,column:0,rowCount:values.length,columnCount:values[0].length}).assign({fill:c.surface,textStyle:{typeface:font,fontSize:24,color:c.ink},margins:{left:16,right:16,top:12,bottom:12}});
 t.cells.block({row:0,column:0,rowCount:1,columnCount:values[0].length}).assign({fill:c.nav,textStyle:{typeface:font,fontSize:24,color:c.surface,bold:true}});return t;
}
function node(s,title,detail,x,y,w=240,h=110,fill=c.subtle){const sh=rect(s,x,y,w,h,fill,c.border);text(s,title,x+14,y+15,w-28,40,24,c.nav,true);text(s,detail,x+14,y+55,w-28,h-55,21,c.muted);return sh;}
function connect(s,a,b,from='right',to='left'){s.shapes.connect(a,b,{kind:'elbow',fromSide:from,toSide:to,line:{fill:c.borderStrong,width:2},tail:{type:'triangle',width:'sm',length:'sm'}});}

let s=slide('Bottleneck\nBusters',1,true);
text(s,'Traffic intervention studies,\nwith decisions you can inspect',70,260,950,170,48,c.surface);
text(s,'Industry Hackathon 2026\nEnergy and Infrastructure Systems',70,508,1000,75,24,c.navText);
notes(s,'0:00–0:20 (20s). Introduce the team and the decision: which intervention deserves a closer engineering study under limited capital? Our prototype supports a planner. No City deployment or field benefit claim. Replace the presenter/team names before the pitch.',[sources.rubric]);

s=slide('The planner’s decision',2);
text(s,'Which intervention fits\nthe budget and the corridor?',68,190,1090,140,48,c.nav,true);
text(s,'Ideal user: municipal transportation planner or consultant engineer.\nReviewer: program manager responsible for capital spending.',68,352,1120,92,27);
text(s,'Product hypothesis: faster preparation, comparison and evidence review.\nExisting engineering tools already support traffic studies.',68,492,1130,90,25,c.muted);
notes(s,'0:20–0:50 (30s). Explain the proposed industrial customer and workflow gap. No firsthand expert validation has been established. Replace with a consented customer quote if obtained. Do not claim cities make arbitrary funding decisions. Upcoming canonical journeys: UJ1 Intervention and Prediction, UJ2 Dashboards, UJ3 External API and resource evidence.',[sources.rubric,'docs/problem_statement.md','constitution/mission.md']);

s=slide('Calgary data and its limits',3);
text(s,'3,987',68,174,390,95,76,c.observed,true);
text(s,'reported incidents in the saved six-month dataset',70,275,1010,55,28);
table(s,[['Evidence','How the prototype uses it'],['City incidents and closures','Study context and incident conditions'],['Signals, volumes, travel times','Location context and observed segment signals'],['Synthetic geometry and derived demand','Explicit model inputs, with calibration pending']],68,360,1144,236,[465,679]);
notes(s,'0:50–1:20 (30s). Show observed data lineage. This figure describes the saved October3 dataset, not a live citywide total. The archive is described by the City as unofficial. Incident reports do not measure arrival flow. Daily 2024 volumes do not establish peak turning counts. Raw observed data stays distinct from derived features and assumed model inputs. New organizer3:26PM guidance rejects fictitious columns added to real data. Separately labeled simulation assumptions remain an eligibility clarification, not a verified exemption.',[sources.data,'data/analysis/sources_manifest.json',sources.updates]);

s=slide('Running architecture',4);
const city=node(s,'City datasets','HTTPS datasets',68,185);
const collector=node(s,'Python collector','Poll, retry, parse, audit',375,185,260);
const db=node(s,'SQLite store','Sources and study history',720,185,290);
const api=node(s,'FastAPI + MCP','Shared application services',375,380,300);
const react=node(s,'React web client','Planner study and review',68,380);
const sumo=node(s,'SUMO adapter','Actual modeled trial metrics',820,380,310);
connect(s,city,collector);connect(s,collector,db);connect(s,db,api,'bottom','top');connect(s,react,api);connect(s,api,sumo);
text(s,'Domain policies stay independent of the UI, database and simulator.\nTimescaleDB is a target. The running store uses SQLite.',68,550,1135,75,24,c.muted);
notes(s,'1:20–1:40 (20s). Explain the implemented architecture, not proposed infrastructure. Collector and API/MCP share application services over the same store. The domain owns policy, the SUMO adapter owns numerical simulation. Native diagram shapes and connectors remain editable. Source discovery for arbitrary cities is future work; do not present it as implemented.',[sources.design,'constitution/architecture.md','backend/app/api.py','backend/app/mcp_server.py']);

s=slide('Autonomous decision and revision',5);
const a=node(s,'Inspect','Check source + assumptions',68,215,205,125);
const b=node(s,'Propose','Bounded options',305,215,205,125);
const d=node(s,'Simulate','Compare with reference',542,215,205,125);
const e=node(s,'Evaluate','Budget + cross-street rule',779,215,205,125);
const f=node(s,'Revise','Retest signal split',1016,215,195,125);
connect(s,a,b);connect(s,b,d);connect(s,d,e);connect(s,e,f);
text(s,'First proposal fails the cross-street constraint.\nThe policy reduces the signal change and tests again.',68,412,1115,105,35,c.brand,true);
text(s,'Deterministic policies call tools and use simulator results.\nFrozen alternatives face paired seeds and demand stress checks.',68,550,1120,70,25,c.muted);
notes(s,'1:40–2:05 (25s). Show the actual action log. These are deterministic policy agents, not fabricated LLM dialogue or RL training. The rubric explicitly permits simulation, optimization and automatic rule revision. The revision must visibly depend on a failed constraint and measured simulator output.',[sources.rubric,'backend/app/application/planner.py','backend/app/domain/evaluation.py']);

s=slide('Live study',6,true);
text(s,'One intersection.\nOne budget.\nA visible decision.',68,205,1110,250,56,c.surface,true);
text(s,'Show the source context, rejected option, revised plan and exported evidence.',68,520,1085,90,31,c.navText);
notes(s,'2:05–3:35 (90s). Switch to the running app. Rehearse one fixed scenario before the pitch; do not wait for a long simulation to finish. 1) Show the selected intersection and input assumptions. 2) Set budget and cross-street constraint. 3) Run or show the clearly labeled precomputed run. 4) Open action log to point to failed first proposal and automatic revision. 5) Read recommended and lowest-delay options and explain the rejection. 6) Export the real report. Replace [LIVE DEMO URL] in rehearsal notes and keep a private backup video/screenshots. A replay remains a replay. Current saved example run1099e73c uses a synthetic corridor standing in for Deerfoot/Glenmore, which is a freeway interchange; it does not validate a real signal intervention there. Prefer a matched signalized site after calibration.',['docs/demo/demo_script.md','backend/app/application/study_summary.py']);

s=slide('Recorded simulation result',7);
text(s,'6.0%',68,177,405,95,76,c.modeled,true);
text(s,'less modeled delay after revision',72,273,720,50,29,c.modeled);
text(s,'$15,000 assumed capital\n+0.24% cross-street delay',820,190,390,120,29,c.assumed);
const chart=s.charts.add('bar',{title:'Mean delay per vehicle (seconds)',titleTextStyle:{fontSize:22,fill:c.ink},position:{left:68,top:357,width:765,height:240},categories:['Reference','First proposal','Revised plan','Extra lane'],series:[{name:'Mean vehicle delay (s)',values:[207.7,258.1,195.1,104.2],fill:c.modeled}],barOptions:{direction:'bar',grouping:'clustered'},hasLegend:false,dataLabels:{showValue:true,position:'outEnd',textStyle:{fontSize:22,fill:c.ink}},xAxis:{textStyle:{fontSize:22,fill:c.muted}},yAxis:{numberFormatCode:'0.0',textStyle:{fontSize:22,fill:c.muted}}});
applyPresentationChartFont(chart,{fontFamily:font});
text(s,'First proposal fails\n30% cross-street rule.\n\nExtra lane fails\n$100,000 budget.',858,354,355,210,25,c.missing);
text(s,'Prior run 1099e73c. Synthetic corridor and derived arrivals. Field effect remains unverified.',68,606,1120,37,20,c.muted);
notes(s,'3:35–4:05 (30s). Recorded output retrieved from the running API on Oct3 at5:24PMMDT, run1099e73c93b943598aedbfe7bbc018e1. Mean delay includes SUMO timeLoss and departure delay according to app model. Revised6.0121%, assumedcapital15000CAD, cross+0.2426%. Firstproposal increases totaldelay24.3673% andcross58.0014%, above30%constraint. Extra lane49.7947%reduction but1200000CADabove100000budget. Values use weighted normal/incident conditions, three evaluationseeds. Replace this slide with the exact final rehearsed report, never silently treat priorrun aslive. Native chart data is editable. No measured Calgary field saving.', ['output/presentation/recorded_result.json','http://127.0.0.1:8008/api/jobs/1099e73c93b943598aedbfe7bbc018e1/report']);

s=slide('A practical pilot',8);
text(s,'One planning team.\nOne calibrated corridor study.',68,184,1120,155,48,c.nav,true);
text(s,'Proposed value: less time assembling and revising an auditable shortlist.\nSuccess measure: analyst hours per comparable engineering study.',68,364,1100,95,28);
text(s,'Next: measured counts and timings, verified costs and resource availability.\nFuture commercial model: consultant or municipal study subscription.',68,491,1115,94,27,c.muted);
notes(s,'4:05–5:00 (55s). Close with a plausible pilot, not a sales claim. Ask for an engineering partner to reproduce one existing corridor study. Customer pain, willingness to pay and subscription pricing remain hypotheses. [REPLACE: consented industry quote, role, date, pain confirmed.] [REPLACE: observed study preparation time and quoted pilot terms.] Three journeys: Intervention and Prediction supports candidate decisions; Dashboards supports monitoring/review; External API and resource evidence brings labor, materials and equipment constraints. Resource providers are not integrated. Unavailable verified labor may exclude construction, but alternative retiming still needs its own eligibility checks. Explain the bounded data contract and provider adapters as future work.',[sources.rubric,'constitution/roadmap.md']);

s=slide('Evidence boundaries',9);
table(s,[['Status','Evidence and limits'],['Observed','Public City rows, retrieval times and source hashes'],['Derived','Parsed lane impacts and incident frequencies'],['Modeled','SUMO delay on synthetic corridor geometry'],['Assumed','Costs, arrival conversions and resource scenarios'],['Missing / unknown','Turning counts, controller timings, validated customer pain']],68,187,1144,370,[285,859]);
text(s,'Source APIs and model outputs stay separate. Engineering review precedes field change.',68,590,1135,40,24,c.muted);
notes(s,'Q&A appendix. Distinguish observed, derived, modeled, assumed and missing evidence without relying only on color. Costs must come from quotes or defensible estimates before a real capital recommendation. The collector runs configured Calgary adapters. General autonomous provider onboarding remains proposed. Missing data may withhold a decision rather than substituting invented measurements. Organizer eligibility clarification about labeled synthetic scenarios remains open.',[sources.data,sources.design,sources.updates]);

s=slide('Demo and submission preparation',10);
text(s,'Final rehearsed run: [RUN ID + report link]\nBackup: [VIDEO URL + 2–5 screenshots]\nCustomer evidence: [ROLE + quote + date]\nCustom-case approval: [ORGANIZER confirmation]',68,190,1135,220,30,c.ink);
text(s,'Submission: Sunday October 4, noon MDT\nPitch: 5 minutes, then 3 minutes Q&A',68,450,1120,100,35,c.nav,true);
text(s,'Organizer approval and final submission remain unverified.',68,585,1120,45,24,c.missing);
notes(s,'Q&A/preparation appendix, not part of the five-minute pitch. Keep placeholders editable and resolve before presentation. Theme mirrors the product tokens with a renderer-safe Liberation Sans font. New organizer guidance: starter optional, ElevenLabs optional prize category, customcase mustreceiveapproval, fictitious realdatasetcolumns rejected. This template doesnotclaimorganizeracceptance. [REPLACE: presentation URL] [REPLACE: repository URL] [REPLACE: teamhandles].', [sources.rubric,'organizer_docs/SUBMISSIONS.md',sources.updates]);

await fs.mkdir(build,{recursive:true});
const candidate=path.join(build,'candidate.pptx');
await(await PresentationFile.exportPptx(p)).save(candidate);
const final=path.join(work,'Bottleneck_Busters_Presentation_Template_v3.pptx');
await finalizePresentation({workspaceDir:repo,candidatePath:candidate,finalPath:final,pythonExecutable:python,integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit','--require-native-table-slide','3','--require-native-table-slide','9'],fontPolicy:{basis:'design',families:[font]},requiredNativeTableOwnerSlides:[3,9],requiredNativeChartOwnerSlides:[7],materializeLiteralChartWorkbooks:true,nativeChartTargetApplication:'powerpoint',verifyArtifactToolImport:true,receiptPath:path.join(repo,'output/.presentation-validation/validation-v3.json')});
console.log(final);
