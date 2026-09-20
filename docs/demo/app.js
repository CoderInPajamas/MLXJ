"use strict";

const bundle = window.JEV_MLX_REPLAY;
const capture = bundle.capture;
const assetRoot = "../assets/browser-demo/";
const scenes = capture.cases.map((record) => ({name:record.name,record}));
scenes.push({name:"state-change-protection",record:capture.state_change_check,concurrency:true});
let currentIndex = 3;
const language = new URLSearchParams(location.search).get("lang") === "zh-CN" ? "zh" : "en";
const byId = (id) => document.getElementById(id);
const escapeHTML = (value) => String(value).replace(/[&<>"']/g,(ch) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[ch]));

const words = {
  en:{brandSubtitle:"Recorded browser decisions",replayBadge:"RECORDED REPLAY",eyebrow:"FROM WORDS TO A VERIFIED CLICK",title:"Small decisions.<br>Recorded in the browser.",intro:"Explore a real local-model run, one decision at a time. Inspect the words, the available choices, and the action that actually happened.",offlineTitle:"A recording, not live inference.",offlineBody:"Everything here comes from the bundled transcript. Changing a scene only reads saved results. No model, server, or network connection is used.",sourceLink:"Inspect original transcript ↗",runLabel:"CAPTURED RUN",modelLabel:"LOCAL MODEL",scopeLabel:"THIS RECORDING",evaluationLink:"Full evaluation & limitations ↗",scenesTitle:"Recorded scenes",selectHint:"SELECT TO INSPECT",initialLink:"Initial desktop — before any decision ↗",utteranceLabel:"ORIGINAL USER UTTERANCE",modelChoiceLabel:"RAW MODEL CHOICE",timeLabel:"RECORDED DECISION TIME",executionLabel:"ACTUAL EXECUTION",captureLabel:"ORIGINAL BROWSER CAPTURE",openCapture:"Open full image ↗",noCaptureTitle:"No screenshot was captured for this scene.",noCaptureBody:"Its original decision, scores, state, and receipt are preserved below. A screenshot from another scene would not be evidence for this one.",scoresTitle:"Candidate scores",scoresNote:"Relative scores over the supplied choices, not calibrated probabilities of correctness. Raw logits are also shown.",candidateLabel:"Candidate ID",scoreLabel:"Score",logitLabel:"Logit",receiptTitle:"Execution receipt",operationTitle:"Recorded browser operation",cacheTitle:"Recorded cache & timing",statesTitle:"Before & observed application state",beforeTitle:"BEFORE",observedTitle:"OBSERVED AFTER",rawTitle:"Complete original record",sourceTitle:"Evidence you can follow.",sourceBody:"This is one fictional browser smoke run, not the held-out model benchmark. The screenshots retain the project's original name at capture time. Nothing in the original evidence has been retouched.",transcriptLink:"Transcript ↗",provenanceLink:"Artifact hashes ↗",videoLink:"Full original WebM recording ↗",realDemoLink:"Run the real local demo ↗",homeLink:"Back to home ↗",hashLabel:"TRANSCRIPT SHA-256",independentNote:"Independent project. Inspired by JEV; no TypeSafe AI affiliation.",count:"16 decisions + 1 concurrency check",scene:"SCENE",check:"SEPARATE CONCURRENCY CHECK",missingUtterance:"The utterance was not stored in this concurrency record.",context:"Recorded context",views:{desktop:"Desktop",library:"Course library",notes:"Field Notes",player:"Course player"},filter:"filter",sort:"order",visible:"visible order",playing:"playing",paused:"paused",loading:"loading",state:"state",cacheHit:"cache hit",cacheMiss:"cold cache",tokens:"tokens reused",margin:"logit margin",executed:"Executed",notExecuted:"No action",staleBlocked:"Stale rejected",receiptRecorded:"Original receipt from the actual DOM-button execution. Model correctness and execution correctness were judged separately.",receiptMissing:"The transcript contains no execution receipt for this decision.",raceReceipt:"The recorded check confirms the old result was not executed. Request overlap was observed; GPU-compute overlap was not measured.",raceContext:"The page changed before the decision response was finalized. Raw model choice and host rejection are shown separately.",noSnapshot:"No matching per-scene screenshot is present in the bundled artifacts.",oldBrand:"Original, unedited capture. The earlier project name is preserved.",screenshotPrefix:"Exact screenshot for this recorded scene",recordOnly:"Historical result — no inference runs on this page.",selected:"selected",no_match:"no match",abstain:"abstained",stale:"stale",rawState:"decision snapshot",unrecorded:"not recorded",previous:"Previous recorded scene",next:"Next recorded scene"},
  zh:{brandSubtitle:"浏览器决策录制回放",replayBadge:"录制回放",eyebrow:"从一句话，到有回执的真实点击",title:"小小的决策。<br>留在浏览器里的真实记录。",intro:"逐条查看一次本地模型的真实运行：原始话语、当时的候选，以及最后确实执行的动作。",offlineTitle:"这是录制回放，不是实时推理。",offlineBody:"所有内容都来自随项目附带的记录。切换场景只读取保存的结果，不调用模型、服务或网络。",sourceLink:"查看原始记录 ↗",runLabel:"录制时间",modelLabel:"当时使用的本地模型",scopeLabel:"本次记录范围",evaluationLink:"完整评测与限制 ↗",scenesTitle:"已录制场景",selectHint:"选择一项查看",initialLink:"初始桌面：任何决策之前 ↗",utteranceLabel:"原始用户话语（保留英文）",modelChoiceLabel:"模型原始选择",timeLabel:"当时测得的决策耗时",executionLabel:"实际执行结果",captureLabel:"原始浏览器截图",openCapture:"查看原尺寸截图 ↗",noCaptureTitle:"这个场景没有单独截图。",noCaptureBody:"下方保留了它的原始决策、分数、状态和回执。其他场景的截图不能作为本场景的证据。",scoresTitle:"候选分数",scoresNote:"这些分数只比较当前候选，不是经过校准的正确概率。右侧同时保留原始 logit。",candidateLabel:"候选 ID",scoreLabel:"相对分数",logitLabel:"Logit",receiptTitle:"实际执行回执",operationTitle:"记录的浏览器操作",cacheTitle:"记录的缓存与耗时",statesTitle:"决策前与实际观察到的状态",beforeTitle:"决策之前",observedTitle:"执行后观察",rawTitle:"完整原始记录",sourceTitle:"每个结果，都有出处。",sourceBody:"这里展示一次虚构场景的浏览器冒烟测试，不是冻结测试集上的模型基准。截图保留了录制时的旧项目名；原始证据未被修图或改写。",transcriptLink:"原始记录 ↗",provenanceLink:"文件哈希与来源 ↗",videoLink:"完整原始 WebM 录像 ↗",realDemoLink:"运行真正的本地 demo ↗",homeLink:"返回主页 ↗",hashLabel:"原始记录 SHA-256",independentNote:"独立维护，受 JEV 启发，与 TypeSafe AI 无官方关联。",count:"16 条决策 + 1 次并发检查",scene:"录制场景",check:"独立的并发状态检查",missingUtterance:"这条并发记录没有保存原始话语。",context:"录制时的上下文",views:{desktop:"桌面",library:"课程库",notes:"笔记窗口",player:"课程播放器"},filter:"筛选",sort:"排序",visible:"可见顺序",playing:"播放中",paused:"已暂停",loading:"加载中",state:"状态版本",cacheHit:"缓存命中",cacheMiss:"冷缓存",tokens:"个 token 已复用",margin:"logit 差值",executed:"已执行",notExecuted:"未执行动作",staleBlocked:"过期已拒绝",receiptRecorded:"这是实际 DOM 按钮执行产生的原始回执。模型是否选对、执行是否正确，分别判断。",receiptMissing:"这条决策的原始记录中没有执行回执。",raceReceipt:"记录确认旧结果没有执行。观察到了决策请求期间的状态变化，未单独测量 GPU 计算重叠。",raceContext:"页面在决策响应完成前发生了变化。模型原始选择与宿主的过期拒绝分开显示。",noSnapshot:"随项目附带的证据中没有与本场景精确对应的单独截图。",oldBrand:"未经修改的原始截图，保留了当时的旧项目名。",screenshotPrefix:"与当前记录精确对应的截图",recordOnly:"历史记录：本页不会运行推理。",selected:"已选择",no_match:"不匹配",abstain:"弃权／待澄清",stale:"已过期",rawState:"决策时快照",unrecorded:"未记录",previous:"上一个录制场景",next:"下一个录制场景"}
};

const titles = {
  "close-with-no-open-object":["Close it, with nothing open","没有打开对象时的 Close it"],
  "open-feature-without-playing-content":["Open the feature, not a course","打开入口与播放内容的区别"],
  "filter-by-category":["Filter the visible courses","筛选当前可见课程"],
  "first-follows-filtered-reversed-visible-order":["First one follows the visible order","First one 遵循当前可见顺序"],
  "pause-ready-player":["Pause the ready player","暂停就绪的播放器"],
  "resume-paused-player":["Resume the paused video","继续已暂停的播放"],
  "rewind-ten-seconds":["Rewind by ten seconds","回退十秒"],
  "question-is-not-a-close-command":["A question is not another action","询问不应变成再次操作"],
  "negation-is-not-an-action":["Respect a negative instruction","否定不能被转成动作"],
  "close-current-player":["Close the current player","关闭当前播放器"],
  "nonexistent-course":["Decline a nonexistent target","拒绝不存在的目标"],
  "close-current-library":["Close the current library","关闭当前课程库"],
  "open-second-object":["Open a different object","打开另一个对象"],
  "close-current-notes":["Close the current notes","关闭当前笔记窗口"],
  "ambiguous-request":["Decline an unclear request","不强行执行模糊请求"],
  "loading-player-has-no-pause-action":["Loading changes allowed actions","加载状态改变可执行候选"],
  "state-change-protection":["Reject a result after the page changes","页面变化后拒绝旧结果"]
};
const captions = {
  "open-feature-without-playing-content":["Captured after the library-opening decision. The feature is open; no course is playing.","在打开课程库的决策后截取：功能入口已打开，没有播放课程。"],
  "first-follows-filtered-reversed-visible-order":["Captured after “First one” selected Orbit Field Notes from the filtered, reversed list. The player is loading.","在 First one 选择筛选并倒序后的 Orbit Field Notes 后截取：播放器正在加载。"],
  "pause-ready-player":["Captured immediately after the recorded pause decision. The player is paused and its receipt reports player.pause.","紧接暂停决策后截取：播放器已暂停，执行回执为 player.pause。"],
  "state-change-protection":["Final capture of the separate state-change check. The old decision is rejected while Field Notes remains open.","独立状态变化检查的最后截图：旧决策被拒绝，笔记窗口保持打开。"]
};

function titleFor(scene) { return titles[scene.name]?.[language === "zh" ? 1 : 0] || scene.name; }
function json(value) { return JSON.stringify(value === undefined ? null : value,null,2); }
function contextFor(scene) {
  const text = words[language];
  if (scene.concurrency) return text.raceContext;
  const state = scene.record.before_state;
  if (!state) return text.unrecorded;
  const parts = [text.views[state.view] || state.view];
  if (state.view === "library") {
    parts.push(`${text.filter}: ${state.library.filter}`,`${text.sort}: ${state.library.sort}`);
    parts.push(`${text.visible}: ${state.library.visible_courses.map((course) => `${course.position}. ${course.title}`).join(" → ")}`);
  }
  if (state.player) parts.push(state.player.course,text[state.player.status] || state.player.status);
  return `${text.context} · ${parts.join(" · ")}`;
}

function renderList() {
  byId("scene-list").innerHTML = scenes.map((scene,index) => `<button type="button" class="scene-button" data-scene="${index}" aria-current="${index === currentIndex}"><span class="scene-number">${scene.concurrency ? "↺" : String(index+1).padStart(2,"0")}</span><span class="scene-copy"><strong>${escapeHTML(titleFor(scene))}</strong><span>${escapeHTML(scene.record.result.raw_selected_id)}</span></span></button>`).join("");
  byId("scene-list").querySelectorAll("button").forEach((button) => button.addEventListener("click",() => selectScene(Number(button.dataset.scene))));
}

function renderScene() {
  const text = words[language];
  const scene = scenes[currentIndex];
  const record = scene.record;
  const result = record.result;
  const receipt = record.execution_receipt;
  byId("scene-counter").textContent = scene.concurrency ? text.check : `${text.scene} ${String(currentIndex+1).padStart(2,"0")} / ${capture.cases.length}`;
  byId("scene-title").textContent = titleFor(scene);
  byId("utterance").textContent = record.utterance ? `“${record.utterance}”` : text.missingUtterance;
  byId("context-note").textContent = contextFor(scene);
  byId("raw-choice").textContent = result.raw_selected_id;
  byId("result-status").textContent = `${text[result.status] || result.status} · ${text.rawState} v${result.state_version}`;
  const elapsed = result.timing.decision_ms;
  byId("decision-time").textContent = Number.isFinite(elapsed) ? `${elapsed.toFixed(1)} ms` : text.unrecorded;
  byId("cache-summary").textContent = `${result.cache.hit ? text.cacheHit : text.cacheMiss} · ${result.cache.reused_tokens} ${text.tokens}`;
  byId("execution-summary").textContent = scene.concurrency ? text.staleBlocked : receipt?.executed ? text.executed : text.notExecuted;
  byId("execution-detail").textContent = receipt?.executed ? `${receipt.action_id} · v${receipt.from_version} → v${receipt.to_version}` : scene.concurrency ? `old_result_not_executed: ${record.old_result_not_executed}` : text.recordOnly;
  const image = byId("capture-image");
  const file = bundle.screenshots_by_case[scene.name];
  image.hidden = !file;
  byId("capture-missing").hidden = Boolean(file);
  byId("open-capture").hidden = !file;
  if (file) {
    image.src = assetRoot + file;
    image.alt = `${text.screenshotPrefix}: ${titleFor(scene)}`;
    byId("open-capture").href = assetRoot + file;
    byId("capture-caption").textContent = `${captions[scene.name][language === "zh" ? 1 : 0]} ${text.oldBrand} · ${file}`;
  } else {
    image.removeAttribute("src");
    byId("open-capture").removeAttribute("href");
    byId("capture-caption").textContent = text.noSnapshot;
  }
  byId("margin").textContent = `${text.margin} ${result.margin.toFixed(3)}`;
  byId("scores").innerHTML = Object.entries(result.raw_scores).sort((a,b) => b[1]-a[1]).map(([id,logit]) => `<tr class="${id === result.raw_selected_id ? "winner" : ""}"><td>${escapeHTML(id)}</td><td>${result.scores[id].toFixed(4)}</td><td>${logit.toFixed(3)}</td></tr>`).join("");
  byId("state-version").textContent = `${text.state} v${result.state_version}`;
  byId("receipt-note").textContent = scene.concurrency ? text.raceReceipt : receipt?.executed ? text.receiptRecorded : text.receiptMissing;
  byId("receipt-json").textContent = json(scene.concurrency ? {old_result_not_executed:record.old_result_not_executed,decision_request_overlap_proven:record.decision_request_overlap_proven,gpu_compute_overlap_measured:record.gpu_compute_overlap_measured} : receipt);
  byId("operation-json").textContent = json(record.browser_operation);
  byId("timing-json").textContent = json({timing:result.timing,cache:result.cache});
  byId("before-json").textContent = record.before_state ? json(record.before_state) : text.unrecorded;
  byId("after-json").textContent = json(record.observed_state);
  byId("raw-json").textContent = json(record);
  byId("previous").disabled = currentIndex === 0;
  byId("next").disabled = currentIndex === scenes.length-1;
  renderList();
}

function selectScene(index) {
  currentIndex = Math.max(0,Math.min(scenes.length-1,index));
  renderScene();
}

function renderLanguage() {
  const text = words[language];
  document.documentElement.lang = language === "zh" ? "zh-CN" : "en";
  document.title = language === "zh" ? "MLXJ — 浏览器决策录制回放" : "MLXJ — Recorded browser decisions";
  document.querySelectorAll("[data-i18n]").forEach((element) => {
    const key = element.dataset.i18n;
    if (key === "title") element.innerHTML = text[key];
    else element.textContent = text[key];
  });
  const links = language === "en"
    ? {home:"../../README.md",evaluation:"../results.md",live:"../http-and-demo.md"}
    : {home:"../../README.zh-CN.md",evaluation:"../results.zh-CN.md",live:"../http-and-demo.zh-CN.md"};
  document.querySelector(".brand").href = links.home;
  document.querySelector('[data-i18n="homeLink"]').href = links.home;
  document.querySelector('[data-i18n="evaluationLink"]').href = links.evaluation;
  document.querySelector('[data-i18n="realDemoLink"]').href = links.live;
  byId("scene-list").setAttribute("aria-label",text.scenesTitle);
  byId("previous").setAttribute("aria-label",text.previous);
  byId("next").setAttribute("aria-label",text.next);
  byId("run-count").textContent = text.count;
  renderScene();
}

byId("run-date").textContent = capture.created_utc.replace("T"," · ").slice(0,21) + " UTC";
byId("run-model").textContent = capture.cases[0].result.model.name;
byId("source-hash").textContent = bundle.source_sha256;
byId("video-link").href = assetRoot + capture.video;
byId("previous").addEventListener("click",() => selectScene(currentIndex-1));
byId("next").addEventListener("click",() => selectScene(currentIndex+1));
renderLanguage();
