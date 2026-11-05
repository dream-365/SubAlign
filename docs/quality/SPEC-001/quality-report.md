# Spec Quality Report

- Target: `docs/specs/SPEC-001-subtitle-timeline-alignment/spec.md`
- Rubric: 1.1.0 (`1e6c4740ed85512b1657e6798e481c893fe015f4ce2a140665ff6ecb2ef7b29e`)
- Target SHA-256: `4247f9bc582cd48619f42beed2d6ebed3892e65c92fc22f7592e8e8dee25c7e7`
- Reviewer session: `979bd64d-371a-4a5a-9c0e-fc1b1238c24f`

**Headline score (core): 100.0**  |  Diagnostic score (all): 99.3

> The auditor verifies evidence presence, section placement, and score arithmetic. It does not judge whether evidence is sufficient or true.

> Normalization covers full-width ASCII, NBSP, and ideographic space; it is not full Unicode NFKC.

| Dimension | Headline | Diagnostic | Weight |
|---|---:|---:|---:|
| 背景落地 | 100.0 | 100.0 | 2 |
| 痛点证据 | 100.0 | 100.0 | 3 |
| 目标可验收 | 100.0 | 100.0 | 3 |
| 非目标边界 | 100.0 | 100.0 | 2 |
| 架构自洽 | 100.0 | 100.0 | 2 |
| 详细设计完整 | 100.0 | 91.7 | 2 |
| NFR 可度量 | 100.0 | 100.0 | 2 |
| 上线可回滚 | 100.0 | 100.0 | 2 |
| 替代方案诚实 | 100.0 | 100.0 | 2 |
| 跨章自洽 | 100.0 | 100.0 | 2 |
| 证据卫生 | 100.0 | 100.0 | 3 |

## 背景落地 (background)

- **bg.current_state** [core, level 2] — 1.1 是否写清了模块职责、核心流程与当前技术栈？
  - evidence `1.1 系统现状`: "1. 从字幕站下载与片名匹配的 SRT 或 ASS。 2. 播放器加载字幕。若整体偏移，用播放器的「字幕延迟」功能以 100ms 或 500ms 为步长调整。 3. 调整后若后段再次错位，退出播放，用字幕编辑器逐行改时间轴，或换一个字幕版本重试。 4. 若新版本仍不匹配，放弃该字幕。"
  - normalized: "1. 从字幕站下载与片名匹配的 SRT 或 ASS。 2. 播放器加载字幕。若整体偏移,用播放器的「字幕延迟」功能以 100ms 或 500ms 为步长调整。 3. 调整后若后段再次错位,退出播放,用字幕编辑器逐行改时间轴,或换一个字幕版本重试。 4. 若新版本仍不匹配,放弃该字幕。"
  - evidence `1.1 系统现状`: "技术栈停留在「播放器 + 文本编辑器」：没有音频分析，没有语音识别，也没有任何自动对齐环节。字幕文件只被当作一串固定时间码，播放器也只把它当作一个可整体平移的文本层。"
  - normalized: "技术栈停留在「播放器 + 文本编辑器」:没有音频分析,没有语音识别,也没有任何自动对齐环节。字幕文件只被当作一串固定时间码,播放器也只把它当作一个可整体平移的文本层。"
  - rationale: 项目尚无实现，1.1 明确说明现状是所替代的人工流程；正文给出四步工作流与技术栈，模块职责在 greenfield 前提下不适用。
- **bg.failure_chain** [core, level 2] — 1.2 是否有从触发到后果的分步失败链？
  - evidence `1.2 核心技术痛点`: "1. 字幕文件来自另一片源，片头长度、帧率或剪辑点与手头视频不同。 2. 播放器把整条字幕视为一个整体，只提供单一全局延迟参数。 3. 前段对齐后，片源差异在后段累积；一次镜头切换、片头剪辑或广告断点就可能产生一个新的固定偏移。 4. 观影者每遇到一个断点就要暂停、重调、继续；断点数量随片源差异增加而增加。 5. 播放器的调整粒度与手动改轴的成本，使「逐段校正」在长片里不可行，最终只能放弃该字幕。"
  - normalized: "1. 字幕文件来自另一片源,片头长度、帧率或剪辑点与手头视频不同。 2. 播放器把整条字幕视为一个整体,只提供单一全局延迟参数。 3. 前段对齐后,片源差异在后段累积;一次镜头切换、片头剪辑或广告断点就可能产生一个新的固定偏移。 4. 观影者每遇到一个断点就要暂停、重调、继续;断点数量随片源差异增加而增加。 5. 播放器的调整粒度与手动改轴的成本,使「逐段校正」在长片里不可行,最终只能放弃该字幕。"
  - rationale: 1.2 用编号 1–5 串联片源差异、全局延迟、后段累积、反复调整直至放弃，构成从触发到后果的完整失败链。
- **bg.trigger** [core, level 2] — 1.3 是否解释了为什么现在做？
  - evidence `1.3 重构/设计动机`: "触发点就是上述《印象派》事故：它暴露了「全局延迟」这一交互模型在分段跳变面前的失效。"
  - normalized: "触发点就是上述《印象派》事故:它暴露了「全局延迟」这一交互模型在分段跳变面前的失效。"
  - evidence `1.3 重构/设计动机`: "若推迟，下次遇到分段错位仍只能手动处理；随着同一部片子的片源版本增多，字幕与片源不匹配只会更常见。"
  - normalized: "若推迟,下次遇到分段错位仍只能手动处理;随着同一部片子的片源版本增多,字幕与片源不匹配只会更常见。"
  - rationale: 以《印象派》事故为触发点，并用 token 时间戳可用、消费级硬件够用、现有工具边界清楚三点解释为何现在做。
- **bg.non_goals** [core, level 2] — 1.4 是否写了不做的后果与本次非目标？
  - evidence `1.4 非目标`: "不做的后果：继续维持「播放器全局延迟 + 手动改轴」，分段错位的片源实际上不可用；只能等待字幕站出现与手头片源完全匹配的版本，而这不受自己控制。"
  - normalized: "不做的后果:继续维持「播放器全局延迟 + 手动改轴」,分段错位的片源实际上不可用;只能等待字幕站出现与手头片源完全匹配的版本,而这不受自己控制。"
  - evidence `1.4 非目标`: "本次非目标："
  - normalized: "本次非目标:"
  - rationale: 先写不做会导致分段错位片源不可用，再列出六条本次非目标，满足后果与边界两项。

## 痛点证据 (pain_evidence)

- **bg.pain_evidence** [core, level 2] — 1.2 是否有至少一条可核实的证据（事故、度量或引述）？
  - evidence `1.2 核心技术痛点`: "具体证据：2026-11 观看纪录片《印象派》时，同一份字幕文件在片头调 +2s 后对齐；播放到中段镜头切换后需要再 +2~3s；后续至少再出现一次跳变。影片文件与字幕文件均在本机，可复现。这不是一次性平移能解决的偏移，而是同一文件内多段不同偏移。"
  - normalized: "具体证据:2026-11 观看纪录片《印象派》时,同一份字幕文件在片头调 +2s 后对齐;播放到中段镜头切换后需要再 +2~3s;后续至少再出现一次跳变。影片文件与字幕文件均在本机,可复现。这不是一次性平移能解决的偏移,而是同一文件内多段不同偏移。"
  - rationale: 给出 2026-11《印象派》事故的时间、具体偏移量、可复现条件，并与失败链的多段不同偏移直接对应。

## 目标可验收 (goal_verifiability)

- **goal.verifiable** [core, level 2] — 2.1 每个 Goal 是否都有验收方式？
  - evidence `2.1 目标`: "- **G1 - 对齐精度**：在 300 行人工标注基准（覆盖整体平移、线性漂移、分段跳变三类，含 SRT 与 ASS、单语与中英双语）上，修正后每行起始时间的绝对误差中位数 ≤ 0.10s、P90 ≤ 0.20s；结束时间同口径。验收方式：'eval/precision.py' 按格式与语言分组输出误差分布，并人工抽查 30 行复核。"
  - normalized: "- **G1 - 对齐精度**:在 300 行人工标注基准(覆盖整体平移、线性漂移、分段跳变三类,含 SRT 与 ASS、单语与中英双语)上,修正后每行起始时间的绝对误差中位数 ≤ 0.10s、P90 ≤ 0.20s;结束时间同口径。验收方式:'eval/precision.py' 按格式与语言分组输出误差分布,并人工抽查 30 行复核。"
  - evidence `2.1 目标`: "- **G5 - 性能**：在 M2 MacBook（16GB）上，100 分钟 1080p 视频使用 whisper.cpp 的 large-v3-turbo GGML 模型，端到端 ≤ 30 分钟，峰值 RSS ≤ 8GB。验收方式：'benchmarks/run.sh' 计时并记录 '/usr/bin/time -l' 的峰值内存。"
  - normalized: "- **G5 - 性能**:在 M2 MacBook(16GB)上,100 分钟 1080p 视频使用 whisper.cpp 的 large-v3-turbo GGML 模型,端到端 ≤ 30 分钟,峰值 RSS ≤ 8GB。验收方式:'benchmarks/run.sh' 计时并记录 '/usr/bin/time -l' 的峰值内存。"
  - rationale: G1–G5 每条都写明验收方式（脚本、回归断言、哈希与 Schema、基准计时）；引文示例覆盖精度与性能两类。
- **goal.quantified** [core, level 2] — 2.1 是否至少有一个 Goal 有数字/单位/明确阈值？
  - evidence `2.1 目标`: "- **G1 - 对齐精度**：在 300 行人工标注基准（覆盖整体平移、线性漂移、分段跳变三类，含 SRT 与 ASS、单语与中英双语）上，修正后每行起始时间的绝对误差中位数 ≤ 0.10s、P90 ≤ 0.20s；结束时间同口径。验收方式：'eval/precision.py' 按格式与语言分组输出误差分布，并人工抽查 30 行复核。"
  - normalized: "- **G1 - 对齐精度**:在 300 行人工标注基准(覆盖整体平移、线性漂移、分段跳变三类,含 SRT 与 ASS、单语与中英双语)上,修正后每行起始时间的绝对误差中位数 ≤ 0.10s、P90 ≤ 0.20s;结束时间同口径。验收方式:'eval/precision.py' 按格式与语言分组输出误差分布,并人工抽查 30 行复核。"
  - rationale: G1 给出 0.10s/0.20s 阈值，G5 给出 30 分钟与 8GB 上限，含数字、单位与明确阈值。
- **goal.count** [extended, level 2] — 2.1 Goals 是否控制在 3–6 个？
  - evidence `2.1 目标`: "按性质分组：可靠性类 G1–G4（精度、分段、不劣化、安全可追溯），性能类 G5。共 5 个目标。"
  - normalized: "按性质分组:可靠性类 G1–G4(精度、分段、不劣化、安全可追溯),性能类 G5。共 5 个目标。"
  - rationale: 共 5 个目标，落在 3–6 区间，并按可靠性 G1–G4 与性能 G5 分类。

## 非目标边界 (non_goal_boundary)

- **nongoal.labeled** [core, level 2] — 2.2 每条 Non-Goal 是否标了本次不做或 Deferred to Phase 2？
  - evidence `2.2 非目标`: "- **NG1 - 交互形态**：不做 GUI、播放器插件与拖拽式界面（本次不做）。"
  - normalized: "- **NG1 - 交互形态**:不做 GUI、播放器插件与拖拽式界面(本次不做)。"
  - evidence `2.2 非目标`: "- **NG4 - 批量与服务化**：不做目录批处理、队列、API 与多用户并发（Deferred to Phase 2）。"
  - normalized: "- **NG4 - 批量与服务化**:不做目录批处理、队列、API 与多用户并发(Deferred to Phase 2)。"
  - rationale: NG1–NG6 每条都以「本次不做」或「Deferred to Phase 2」标注；引文分别覆盖两种标注。
- **nongoal.not_dumping_ground** [extended, level 2] — 2.2 非目标是否能追溯到痛点或边界？
  - evidence `2.2 非目标`: "- **NG2 - ASS 高级特性**：不重算卡拉OK逐字标签、绘图指令与矢量动画的时间；遇到时保留原字段并按 4.6 告警（本次不做）。"
  - normalized: "- **NG2 - ASS 高级特性**:不重算卡拉OK逐字标签、绘图指令与矢量动画的时间;遇到时保留原字段并按 4.6 告警(本次不做)。"
  - evidence `2.2 非目标`: "- **NG6 - 多语言同等精度**：中英以外语言可以运行，但不承诺达到 G1 的精度指标（Deferred to Phase 2）。"
  - normalized: "- **NG6 - 多语言同等精度**:中英以外语言可以运行,但不承诺达到 G1 的精度指标(Deferred to Phase 2)。"
  - rationale: 六条非目标分别对应 1.4 的范围边界、3.4 的 ASS/语言选型约束或 5.5 的不支持项，无与痛点无关的条目。

## 架构自洽 (architecture)

- **arch.solution_shape** [core, level 2] — 第 3 章是否有本次变更的拓扑或等价的模块/数据流描述？
  - evidence `3. 架构设计与核心方案`: "- **对齐层**：把每个字幕行或双语组选出的锚点文本与 token 流做相似度对齐，产出音频起止锚点、匹配率与置信度。"
  - normalized: "- **对齐层**:把每个字幕行或双语组选出的锚点文本与 token 流做相似度对齐,产出音频起止锚点、匹配率与置信度。"
  - evidence `3. 架构设计与核心方案`: "7. 拟合层用 high-confidence 锚点计算残差序列，选择常量、线性或分段模型，并为低置信行在同段内插值。"
  - normalized: "7. 拟合层用 high-confidence 锚点计算残差序列,选择常量、线性或分段模型,并为低置信行在同段内插值。"
  - rationale: 第 3 章给出 mermaid 管线拓扑，并在 3.2/3.3 写明各层职责与九步数据流，覆盖本次变更范围。
- **arch.topology** [extended, level 2] — 3.1 拓扑图是否让每个模块有一句职责？
  - evidence `3.2 核心模块职责`: "- **媒体层**：探测视频时长与音轨，抽取 16kHz / 单声道 / PCM s16le WAV，管理临时文件；识别层只接受这一种格式，原始音轨不得直接送入 whisper.cpp。"
  - normalized: "- **媒体层**:探测视频时长与音轨,抽取 16kHz / 单声道 / PCM s16le WAV,管理临时文件;识别层只接受这一种格式,原始音轨不得直接送入 whisper.cpp。"
  - evidence `3.2 核心模块职责`: "- **输出层**：按模型写回新 SRT 或 ASS，保留非时间字段，生成 JSON 报告；保证输入只读、输出原子替换。"
  - normalized: "- **输出层**:按模型写回新 SRT 或 ASS,保留非时间字段,生成 JSON 报告;保证输入只读、输出原子替换。"
  - rationale: 3.1 的 mermaid 图列出全部模块，3.2 为每个模块给出一句职责；引文示例为媒体层与输出层职责。
- **arch.change_set** [extended, level 2] — 第 3 章是否写清新增/改造/保持不变？
  - evidence `3. 架构设计与核心方案`: "本次变更全部落在 SubAlign 分析管线内部：整条管线都是新增的，外部系统与输入输出边界不变。"
  - normalized: "本次变更全部落在 SubAlign 分析管线内部:整条管线都是新增的,外部系统与输入输出边界不变。"
  - rationale: 明确整条分析管线为新增、外部系统与输入输出边界保持不变；因属新建项目，无改造项。
- **arch.rationale** [extended, level 2] — 关键选型是否有理由，详细对比指向第 7 章？
  - evidence `3.4 关键选型与约束`: "- **选 whisper.cpp 的 DTW token 时间戳，而不是 WhisperX 的 wav2vec2 强制对齐**：whisper.cpp 是单二进制、可用 Metal 加速、GGML 模型可离线分发，已经是本机现有工具链；WhisperX 需要 Python/PyTorch 运行时，部署更重。代价是 whisper.cpp 的 token 时间戳来自 cross-attention/DTW，边界精度低于专用强制对齐，且随语言与音频质量波动。因此方案不把单个 token 的边界当作最终精度，而是用行级锚点、多行残差拟合与低置信插值抵消系统性偏差。识别层默认启用 DTW token 时间戳；关闭时退回启发式 token 时间戳，并在报告中标注。若实验发现 token 边界不足以支撑 G1，按附录 A 的兜底路径处理。详细对比见 7.5。"
  - normalized: "- **选 whisper.cpp 的 DTW token 时间戳,而不是 WhisperX 的 wav2vec2 强制对齐**:whisper.cpp 是单二进制、可用 Metal 加速、GGML 模型可离线分发,已经是本机现有工具链;WhisperX 需要 Python/PyTorch 运行时,部署更重。代价是 whisper.cpp 的 token 时间戳来自 cross-attention/DTW,边界精度低于专用强制对齐,且随语言与音频质量波动。因此方案不把单个 token 的边界当作最终精度,而是用行级锚点、多行残差拟合与低置信插值抵消系统性偏差。识别层默认启用 DTW token 时间戳;关闭时退回启发式 token 时间戳,并在报告中标注。若实验发现 token 边界不足以支撑 G1,按附录 A 的兜底路径处理。详细对比见 7.5。"
  - rationale: whisper.cpp/DTW 选型给出理由、代价与兜底，并明确「详细对比见 7.5」；其余选型也在 3.4 给出理由。
- **arch.references_source** [extended, level 2] — 第 3 章是否引用 depends_on 架构文档，而不是自行展开其全局结构？
  - evidence `3. 架构设计与核心方案`: "全局分层、模块边界与技术栈见 'docs/architecture/system.md'（Approved）。本次变更全部落在 SubAlign 分析管线内部：整条管线都是新增的，外部系统与输入输出边界不变。"
  - normalized: "全局分层、模块边界与技术栈见 'docs/architecture/system.md'(Approved)。本次变更全部落在 SubAlign 分析管线内部:整条管线都是新增的,外部系统与输入输出边界不变。"
  - rationale: depends_on 指向 docs/architecture/system.md，第 3 章引用其承载全局结构，只展开本次新增管线内部职责与选型。

## 详细设计完整 (detailed_design)

- **design.contract** [core, level 2] — 第 4 章是否至少有一份数据模型或接口契约？
  - evidence `4. 详细设计`: "subalign align --video <path> --subtitle <path.srt\|path.ass> --out <path.srt\|path.ass>"
  - normalized: "subalign align --video <path> --subtitle <path.srt\|path.ass> --out <path.srt\|path.ass>"
  - evidence `4. 详细设计`: "\| AsrToken \| text \| string \| 是 \| 归一化后非空 \|"
  - normalized: "\| AsrToken \| text \| string \| 是 \| 归一化后非空 \|"
  - rationale: 第 4 章同时提供 CLI 参数契约与 AsrToken/SubtitleCue 等数据模型字段表，满足至少一份契约的要求。
- **design.data_model** [extended, level 2] — 4.3 数据模型是否有字段类型、必填与校验？
  - evidence `4.3 数据模型与契约`: "\| SubtitleCue \| start / end \| float \| 是 \| '0 ≤ start < end'；ASS 写入时四舍五入到 0.01s \|"
  - normalized: "\| SubtitleCue \| start / end \| float \| 是 \| '0 ≤ start < end';ASS 写入时四舍五入到 0.01s \|"
  - evidence `4.3 数据模型与契约`: "\| AsrToken \| score \| float \| 否 \| '[0, 1]'，缺失按 0 处理 \|"
  - normalized: "\| AsrToken \| score \| float \| 否 \| '[0, 1]',缺失按 0 处理 \|"
  - rationale: 字段表逐行给出类型、必填与校验规则；引文展示时间字段与可选 score 的约束。
- **design.interface** [extended, level 2] — 4.4 接口是否有请求/响应/状态码或方法签名？
  - evidence `4.4 接口与协议`: "\| Media \| 'extract_audio(video) -> AudioInfo' \| 视频路径 \| 16kHz / 单声道 / PCM s16le WAV 路径、时长、采样率 \| 'ERR_NO_AUDIO' / 'ERR_MEDIA_DECODE' / 'ERR_MEDIA_FORMAT' \|"
  - normalized: "\| Media \| 'extract_audio(video) -> AudioInfo' \| 视频路径 \| 16kHz / 单声道 / PCM s16le WAV 路径、时长、采样率 \| 'ERR_NO_AUDIO' / 'ERR_MEDIA_DECODE' / 'ERR_MEDIA_FORMAT' \|"
  - evidence `4.4 接口与协议`: "\| 3 \| 锚点覆盖率不足，放弃修正 \| 否 \|"
  - normalized: "\| 3 \| 锚点覆盖率不足,放弃修正 \| 否 \|"
  - rationale: 4.4 的模块契约表给出方法签名、输入输出与失败语义，CLI 退出码表补齐状态码。
- **design.sequence** [extended, level 2] — 4.5 复杂流程是否有时序图或等价分步说明？
  - evidence `4.5 核心流程与时序`: "正常路径与覆盖不足的异常路径："
  - normalized: "正常路径与覆盖不足的异常路径:"
  - evidence `4.5 核心流程与时序`: "C-->>U: ERR_LOW_COVERAGE，写报告但不写字幕"
  - normalized: "C-->>U: ERR_LOW_COVERAGE,写报告但不写字幕"
  - rationale: 4.5 提供 mermaid 时序图，并用 alt 分支覆盖覆盖率 <0.30 的异常路径；引文即该分支。
- **design.errors** [extended, level 1] — 4.6 每个错误码是否有触发场景与处理策略？
  - evidence `4.6 异常处理与错误码`: "\| 'ERR_AMBIGUOUS_FIT' \| 保留给未来其他分段方法；当前鲁棒分段模型不主动触发 \| 保留错误码与退出码 \| 4 \|"
  - normalized: "\| 'ERR_AMBIGUOUS_FIT' \| 保留给未来其他分段方法;当前鲁棒分段模型不主动触发 \| 保留错误码与退出码 \| 4 \|"
  - evidence `4.6 异常处理与错误码`: "\| 'ERR_LOW_COVERAGE' \| high-confidence 锚点占比 < 30% \| 写报告，不写字幕；提示检查语言或片源 \| 3 \|"
  - normalized: "\| 'ERR_LOW_COVERAGE' \| high-confidence 锚点占比 < 30% \| 写报告,不写字幕;提示检查语言或片源 \| 3 \|"
  - rationale: 多数错误码都有触发场景与处理策略；但 ERR_AMBIGUOUS_FIT 只写「保留给未来」，没有可触发的真实场景与对应处理策略。
  - missing: 为 ERR_AMBIGUOUS_FIT 定义具体的触发条件和处理策略，或从错误码表中删除；其余错误码已达标。

## NFR 可度量 (nfr)

- **nfr.measurable** [core, level 2] — 第 5 章每条 NFR 是否有数字、单位或验收方式？
  - evidence `5. 非功能性需求`: "**端到端耗时**：100 分钟 1080p、whisper.cpp large-v3-turbo GGML、M2 16GB，≤ 30 分钟。[estimated]"
  - normalized: "**端到端耗时**:100 分钟 1080p、whisper.cpp large-v3-turbo GGML、M2 16GB,≤ 30 分钟。[estimated]"
  - evidence `5. 非功能性需求`: "**幂等性**：对已修正过且模型应判为 constant/0 的字幕再次运行，逐行 '\|delta\| ≤ 0.05s'，报告模型为 'constant' 且 'intercept' 接近 0。"
  - normalized: "**幂等性**:对已修正过且模型应判为 constant/0 的字幕再次运行,逐行 '\|delta\| ≤ 0.05s',报告模型为 'constant' 且 'intercept' 接近 0。"
  - evidence `5. 非功能性需求`: "**结构化报告**：每次运行产出 4.3 定义的 JSON 报告，字段完整率 100%；报告通过仓库内 JSON Schema 校验。"
  - normalized: "**结构化报告**:每次运行产出 4.3 定义的 JSON 报告,字段完整率 100%;报告通过仓库内 JSON Schema 校验。"
  - evidence `5. 非功能性需求`: "**输入保护**：输入文件以只读打开，运行前后 SHA-256 必须一致；写回目标与输入路径相同时直接拒绝。"
  - normalized: "**输入保护**:输入文件以只读打开,运行前后 SHA-256 必须一致;写回目标与输入路径相同时直接拒绝。"
  - rationale: 性能、精度、幂等与报告完整性均有数字/单位或可执行断言；安全项以 SHA-256 一致性等明确判定条件验收。
- **nfr.coverage** [core, level 2] — 第 5 章是否覆盖性能、可靠性、可观测性、安全，或说明不适用？
  - evidence `5. 非功能性需求`: "**端到端耗时**：100 分钟 1080p、whisper.cpp large-v3-turbo GGML、M2 16GB，≤ 30 分钟。[estimated]"
  - normalized: "**端到端耗时**:100 分钟 1080p、whisper.cpp large-v3-turbo GGML、M2 16GB,≤ 30 分钟。[estimated]"
  - evidence `5. 非功能性需求`: "**原子性**：输出先写同目录临时文件，'fsync' 后重命名；进程被中断时最多留下临时文件，不留下半截字幕文件。"
  - normalized: "**原子性**:输出先写同目录临时文件,'fsync' 后重命名;进程被中断时最多留下临时文件,不留下半截字幕文件。"
  - evidence `5. 非功能性需求`: "**阶段计时**：报告记录 'media'、'asr'、'align'、'fit'、'write' 五个阶段的秒数，精度到 0.01s。"
  - normalized: "**阶段计时**:报告记录 'media'、'asr'、'align'、'fit'、'write' 五个阶段的秒数,精度到 0.01s。"
  - evidence `5. 非功能性需求`: "**本地优先**：运行期不向任何远端发送音视频、字幕或报告；仅首次下载模型时访问网络，且需显式触发。"
  - normalized: "**本地优先**:运行期不向任何远端发送音视频、字幕或报告;仅首次下载模型时访问网络,且需显式触发。"
  - rationale: 5.1–5.4 分别给出性能、可靠性、可观测性与安全的具体要求，四类均有正文覆盖。
- **nfr.honesty** [core, level 2] — 未实测的指标是否标了 [estimated] 或 未实现？
  - evidence `5. 非功能性需求`: "**端到端耗时**：100 分钟 1080p、whisper.cpp large-v3-turbo GGML、M2 16GB，≤ 30 分钟。[estimated]"
  - normalized: "**端到端耗时**:100 分钟 1080p、whisper.cpp large-v3-turbo GGML、M2 16GB,≤ 30 分钟。[estimated]"
  - evidence `5. 非功能性需求`: "**临时磁盘**：单次运行 ≤ 2GB（16kHz 单声道 WAV 约 190MB/100 分钟，余量留给模型与缓存）。[estimated]"
  - normalized: "**临时磁盘**:单次运行 ≤ 2GB(16kHz 单声道 WAV 约 190MB/100 分钟,余量留给模型与缓存)。[estimated]"
  - rationale: 5.1 的四项未实测指标全部标 [estimated]，未把目标写成已达成。

## 上线可回滚 (rollout)

- **rollout.release** [core, level 2] — 6.1 是否有发布策略与灰度节奏？
  - evidence `6.1 发布与灰度`: "发布形态：本地 CLI，git tag 'v0.1.0'，通过 'uv tool install' 或源码虚拟环境安装；不提供常驻服务。"
  - normalized: "发布形态:本地 CLI,git tag 'v0.1.0',通过 'uv tool install' 或源码虚拟环境安装;不提供常驻服务。"
  - evidence `6.1 发布与灰度`: "灰度按「写回权限」逐级放开，而不是按流量："
  - normalized: "灰度按「写回权限」逐级放开,而不是按流量:"
  - rationale: 6.1 给出本地 CLI + git tag 的发布形态，并按报告模式、单片写回、日常使用三级灰度，附推进条件与观察指标。
- **rollout.migration** [core, level 2] — 6.2 是否有迁移/兼容方案，或说明无需迁移？
  - evidence `6.2 数据迁移与兼容性`: "无需数据迁移：本工具不维护数据库、不保存历史状态，每次运行都是「输入文件 → 新输出文件」。"
  - normalized: "无需数据迁移:本工具不维护数据库、不保存历史状态,每次运行都是「输入文件 → 新输出文件」。"
  - evidence `6.2 数据迁移与兼容性`: "- 输入字幕只读，输出必须为新路径；不支持原地覆盖，因此不存在旧数据被改写的迁移风险。"
  - normalized: "- 输入字幕只读,输出必须为新路径;不支持原地覆盖,因此不存在旧数据被改写的迁移风险。"
  - rationale: 明确无需数据迁移并说明不维护数据库/历史状态，同时给出只读输入、新路径输出与编码沿用的兼容策略。
- **rollout.smoke** [core, level 2] — 6.3 是否有冒烟清单与观察指标？
  - evidence `6.3 上线验证与冒烟`: "1. 'python -m pytest -q'：单元测试与 fixture 回归全部通过。"
  - normalized: "1. 'python -m pytest -q':单元测试与 fixture 回归全部通过。"
  - evidence `6.3 上线验证与冒烟`: "观察指标：退出码分布、'coverage'、选中模型、'warnings' 数量、人工抽查通过率。任一项低于 6.1 的推进条件即停止并回退。"
  - normalized: "观察指标:退出码分布、'coverage'、选中模型、'warnings' 数量、人工抽查通过率。任一项低于 6.1 的推进条件即停止并回退。"
  - rationale: 6.3 列出七步冒烟清单（测试、fixture、格式、断言、双语、真片、Schema/哈希），并给出观察指标与停止条件。
- **rollout.rollback_trigger** [core, level 2] — 6.4 回滚触发条件是否是可观测数字？
  - evidence `6.4 回滚与熔断`: "- 回归集上任一 fixture 出现 ≥5% 的字幕行位移 > 100ms，或新增断点 ≥1 个。"
  - normalized: "- 回归集上任一 fixture 出现 ≥5% 的字幕行位移 > 100ms,或新增断点 ≥1 个。"
  - evidence `6.4 回滚与熔断`: "- 覆盖率 < 30% 却仍然产生了输出字幕文件。"
  - normalized: "- 覆盖率 < 30% 却仍然产生了输出字幕文件。"
  - rationale: 触发条件均为可观测数字或明确断言：≥5% 行位移 >100ms、新增断点 ≥1、SHA-256 不一致、覆盖率 <30% 等。
- **rollout.rollback_steps** [core, level 2] — 6.4 回滚步骤是否可执行？
  - evidence `6.4 回滚与熔断`: "1. 删除本次产生的输出字幕与报告；输入文件从未被写入，无需恢复。"
  - normalized: "1. 删除本次产生的输出字幕与报告;输入文件从未被写入,无需恢复。"
  - evidence `6.4 回滚与熔断`: "2. 回退版本：已发布过上一版本时，执行 'git checkout <上一 tag>' 或 'uv tool install subalign==<上一版本>'；首版尚无上一版本时，执行 'git checkout <发布前提交>'，或直接 'uv tool uninstall subalign' 回到未安装状态。"
  - normalized: "2. 回退版本:已发布过上一版本时,执行 'git checkout <上一 tag>' 或 'uv tool install subalign==<上一版本>';首版尚无上一版本时,执行 'git checkout <发布前提交>',或直接 'uv tool uninstall subalign' 回到未安装状态。"
  - rationale: 四步回滚给出可执行动作：删除产物、按 tag/版本回退或卸载、重跑冒烟、记录 changelog。

## 替代方案诚实 (alternatives)

- **alts.status_quo** [core, level 2] — 第 7 章是否有 Status Quo 及其成本/风险？
  - evidence `7. 替代方案与权衡`: "- **成本与风险**：每个断点都要暂停重调；长片的分段校正不可行；手动改轴无法保证 0.1s 精度；最终常见结果是放弃字幕。触发阈值已经在 1.2 的事故中出现：同一文件内出现两次以上跳变，该流程即失效。"
  - normalized: "- **成本与风险**:每个断点都要暂停重调;长片的分段校正不可行;手动改轴无法保证 0.1s 精度;最终常见结果是放弃字幕。触发阈值已经在 1.2 的事故中出现:同一文件内出现两次以上跳变,该流程即失效。"
  - rationale: 7.1 写明 Status Quo 的思路、优点以及成本与风险，并给出「两次以上跳变即失效」的触发阈值。
- **alts.rejected** [core, level 2] — 第 7 章是否至少有一个被否决方案，且淘汰原因对应当前约束？
  - evidence `7. 替代方案与权衡`: "- **淘汰为唯一方案的原因**：时间信号来自「有声/无声」，不读取字幕文本；字幕行边界只能近似到语音段边界，难以稳定到 0.1s；分段需要调 split 惩罚，不同片源要换参数；静音、音乐与环境声多的纪录片会使 VAD 锚点变稀；不提供逐行置信度，出错时无法定位。它仍是本方案必须对照的基线，见 G2。"
  - normalized: "- **淘汰为唯一方案的原因**:时间信号来自「有声/无声」,不读取字幕文本;字幕行边界只能近似到语音段边界,难以稳定到 0.1s;分段需要调 split 惩罚,不同片源要换参数;静音、音乐与环境声多的纪录片会使 VAD 锚点变稀;不提供逐行置信度,出错时无法定位。它仍是本方案必须对照的基线,见 G2。"
  - evidence `7. 替代方案与权衡`: "- **淘汰原因**：依赖准确的发音词典与文本-音频一一对应假设；长片中背景音乐、音效与多人重叠会破坏对齐；公开对比中 aeneas 的中位结束边界误差约 2s（见 7.8）；对中文需要额外的分词与拼音词典工程，超出本次范围。"
  - normalized: "- **淘汰原因**:依赖准确的发音词典与文本-音频一一对应假设;长片中背景音乐、音效与多人重叠会破坏对齐;公开对比中 aeneas 的中位结束边界误差约 2s(见 7.8);对中文需要额外的分词与拼音词典工程,超出本次范围。"
  - rationale: 7.2–7.4 给出三个被否方案；引文展示 VAD 方案因不读字幕文本、边界精度与调参问题被淘汰，对应当前 0.1s 与分段约束。
- **alts.matrix** [core, level 2] — 第 7 章是否有与约束对应的权衡矩阵？
  - evidence `7. 替代方案与权衡`: "\| 维度 \| Status Quo \| A：VAD 对齐 \| B：文本强制对齐 \| C：纯文本/LLM \| D：whisper.cpp + 文本 \|"
  - normalized: "\| 维度 \| Status Quo \| A:VAD 对齐 \| B:文本强制对齐 \| C:纯文本/LLM \| D:whisper.cpp + 文本 \|"
  - evidence `7. 替代方案与权衡`: "\| 分段跳变自动化 \| 差 \| 中（需调参） \| 差 \| 差 \| **好** \|"
  - normalized: "\| 分段跳变自动化 \| 差 \| 中(需调参) \| 差 \| 差 \| **好** \|"
  - rationale: 7.7 矩阵以行级 0.1s、分段自动化、静音鲁棒性、无需参考字幕、成本与可解释性等约束为维度比较五个方案。
- **alts.consistency** [core, level 2] — 第 7 章结论是否与 Goals、架构选型一致？
  - evidence `7. 替代方案与权衡`: "- **与 Goals 的对应**：G1 由行级锚点与整段拟合支撑；G2 由变点检测支撑；G3 由「宁可不改」与已对齐回归支撑；G4 由报告与原子写回支撑；G5 由单进程串行与 WAV 预处理约束。"
  - normalized: "- **与 Goals 的对应**:G1 由行级锚点与整段拟合支撑;G2 由变点检测支撑;G3 由「宁可不改」与已对齐回归支撑;G4 由报告与原子写回支撑;G5 由单进程串行与 WAV 预处理约束。"
  - rationale: 7.5 明确方案 D 与 G1–G5 的逐条对应，7.7 结论也以同一组约束选择 D，与第 3 章选型一致。

## 跨章自洽 (cross_consistency)

- **x.goals_trace** [core, level 2] — 后续章节是否逐条回应 Goals？
  - evidence `全文`: "- **与 Goals 的对应**：G1 由行级锚点与整段拟合支撑；G2 由变点检测支撑；G3 由「宁可不改」与已对齐回归支撑；G4 由报告与原子写回支撑；G5 由单进程串行与 WAV 预处理约束。"
  - normalized: "- **与 Goals 的对应**:G1 由行级锚点与整段拟合支撑;G2 由变点检测支撑;G3 由「宁可不改」与已对齐回归支撑;G4 由报告与原子写回支撑;G5 由单进程串行与 WAV 预处理约束。"
  - rationale: 7.5 的「与 Goals 的对应」逐条列出 G1–G5 的支撑设计，且第 3/4 章有对应的拟合、报告与串行实现描述。
- **x.nfr_arch** [core, level 2] — NFR 与架构、选型是否一致？
  - evidence `全文`: "- **精度优先于吞吐**：单文件、单进程、串行阶段；不引入队列与并行，避免为性能牺牲可解释性。"
  - normalized: "- **精度优先于吞吐**:单文件、单进程、串行阶段;不引入队列与并行,避免为性能牺牲可解释性。"
  - evidence `全文`: "- **全程本地运行**：音视频不出本机，除首次下载模型外不访问网络；这是隐私约束，也是个人工具的部署前提。"
  - normalized: "- **全程本地运行**:音视频不出本机,除首次下载模型外不访问网络;这是隐私约束,也是个人工具的部署前提。"
  - evidence `全文`: "**端到端耗时**：100 分钟 1080p、whisper.cpp large-v3-turbo GGML、M2 16GB，≤ 30 分钟。[estimated]"
  - normalized: "**端到端耗时**:100 分钟 1080p、whisper.cpp large-v3-turbo GGML、M2 16GB,≤ 30 分钟。[estimated]"
  - evidence `全文`: "**本地优先**：运行期不向任何远端发送音视频、字幕或报告；仅首次下载模型时访问网络，且需显式触发。"
  - normalized: "**本地优先**:运行期不向任何远端发送音视频、字幕或报告;仅首次下载模型时访问网络,且需显式触发。"
  - rationale: 5.1 的 30 分钟目标对应 3.4「单文件、单进程、串行」，5.4 的本地优先对应 3.4「全程本地运行」，无矛盾。
- **x.rollback_release** [core, level 2] — 回滚与发布策略是否一致？
  - evidence `全文`: "灰度按「写回权限」逐级放开，而不是按流量："
  - normalized: "灰度按「写回权限」逐级放开,而不是按流量:"
  - evidence `全文`: "2. 回退版本：已发布过上一版本时，执行 'git checkout <上一 tag>' 或 'uv tool install subalign==<上一版本>'；首版尚无上一版本时，执行 'git checkout <发布前提交>'，或直接 'uv tool uninstall subalign' 回到未安装状态。"
  - normalized: "2. 回退版本:已发布过上一版本时,执行 'git checkout <上一 tag>' 或 'uv tool install subalign==<上一版本>';首版尚无上一版本时,执行 'git checkout <发布前提交>',或直接 'uv tool uninstall subalign' 回到未安装状态。"
  - evidence `全文`: "3. 用 6.3 的冒烟清单重跑 8 个 fixture，确认行为回到上一版本。"
  - normalized: "3. 用 6.3 的冒烟清单重跑 8 个 fixture,确认行为回到上一版本。"
  - rationale: 发布按写回权限分三级灰度，回滚按已发布 tag 或卸载回退并能重跑同一冒烟集，二者在版本与验证口径上一致。

## 证据卫生 (evidence_hygiene)

- **x.no_placeholders** [core, level 2] — 是否没有把 无 / ... / 待补充 / TBD 当作实质回答？
  - evidence `全文`: "- **无遥测**：不采集使用数据，不写用户目录以外的路径。"
  - normalized: "- **无遥测**:不采集使用数据,不写用户目录以外的路径。"
  - evidence `全文`: "无需数据迁移：本工具不维护数据库、不保存历史状态，每次运行都是「输入文件 → 新输出文件」。"
  - normalized: "无需数据迁移:本工具不维护数据库、不保存历史状态,每次运行都是「输入文件 → 新输出文件」。"
  - rationale: 全文未用 无/.../待补充/TBD 作为实质回答；引文中的「无遥测」「无需数据迁移」都带有具体说明。
- **x.no_code** [core, level 2] — 是否没有堆砌实现代码、测试日志或偶发报错？
  - evidence `全文`: "报告的最小 JSON 形状（只列字段，不代表实现）："
  - normalized: "报告的最小 JSON 形状(只列字段,不代表实现):"
  - rationale: 正文只有 mermaid 图、CLI 用法、字段表与 JSON 形状示例，未堆砌实现代码、测试日志或偶发报错。
- **x.numbers_sourced** [core, level 2] — 关键数字是否有出处，或标了 [estimated]？
  - evidence `全文`: "**端到端耗时**：100 分钟 1080p、whisper.cpp large-v3-turbo GGML、M2 16GB，≤ 30 分钟。[estimated]"
  - normalized: "**端到端耗时**:100 分钟 1080p、whisper.cpp large-v3-turbo GGML、M2 16GB,≤ 30 分钟。[estimated]"
  - evidence `全文`: "- 多种强制对齐工具的词边界误差对比（WhisperX 常见 60–150ms，aeneas 中位结束边界误差约 2s；用于说明 token 时间戳与强制对齐的精度差异）：<https://jishuzhan.net/article/2099666343898042370>"
  - normalized: "- 多种强制对齐工具的词边界误差对比(WhisperX 常见 60–150ms,aeneas 中位结束边界误差约 2s;用于说明 token 时间戳与强制对齐的精度差异):<https://jishuzhan.net/article/2099666343898042370>"
  - rationale: 未实测的性能与资源数字均标 [estimated]；外部工具误差数字在 7.8 给出链接出处。
- **x.no_fabricated_refs** [core, level 2] — 是否没有捏造 SPEC 引用、depends_on 目标或 M<N>？
  - evidence `全文`: "depends_on:   - docs/architecture/system.md"
  - normalized: "depends_on: - docs/architecture/system.md"
  - evidence `全文`: "全局分层、模块边界与技术栈见 'docs/architecture/system.md'（Approved）。"
  - normalized: "全局分层、模块边界与技术栈见 'docs/architecture/system.md'(Approved)。"
  - rationale: 引用限于 depends_on 的 docs/architecture/system.md、想法文档与 7.8 外链，未出现 SPEC 伪造引用或 M<N> 标记。

## Audit failures

None.
