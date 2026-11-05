# 实验结果

## 实验 1：《印象派》S01E02 单点验证

| 字段 | 内容 |
| --- | --- |
| 影片 / 字幕 | `The.Impressionists...S01E02.The.Great.Outdoors.2160p.SDR.WEB-DL.AAC2.0.H.264-NTb.mkv`（59.3 分钟，AAC 48k 立体声）；同名字幕 `.简体&英文.ass`（UTF-16，851 个 cue，cue 内中英双语） |
| 格式 / 语言 | ASS；中英双语；ASR 语言 en |
| 模型 | whisper.cpp 1.9.5-dev，`ggml-large-v3-turbo.bin`（SHA-256 `1fc70f77...e2bc69`），ffmpeg 9.0.2 |
| 选中模型 | `linear`：intercept `-44.990s`，slope `0.004538`（约 0.45% 漂移） |
| 覆盖率 | 88.1%（high 750 / medium 60 / low 41） |
| 模型 RMSE | 1.084s |
| 断点 | 0（linear 模型） |
| 双语组 | 3 组（字幕主要是 cue 内两行，不走组模式） |
| 输出 / 报告 | `.local/experiments/impressionists/S01E02.fixed.ass` / `S01E02.report.json` |

### 人工核对

从 780s、1600s、3250s 各抽 120–140 秒音频，用同一模型重新识别，与字幕英文行对齐：

| 视频时间 | ASR 片段 | 字幕时间 | 实测偏移 | linear 预测 |
| --- | --- | --- | --- | --- |
| 780s | "But the really important thing about it is its colour." | 821.15s | -41.15s | -41.42s |
| 1600s | "Renoir's Joie de Vivre is surely contagious." | 1636.91s | -36.91s | -37.63s |
| 3250s | "Mone had a eureka moment." | 3277.52s | -27.52s | -30.11s |
| 3250s | "Putting on his poshest clothes," | 3326.60s | -30.0s | -29.89s |

修复后的输出中，cue 800（"Putting on his poshest clothes"）落在 `3296.71s`，与 ASR 的 `3296.6s` 相差约 **0.1s**。

### 人工校准

用户实际观看后反馈：字幕整体**快约 0.6s**（字幕比画面早出现）。用 `--shift 0.6` 重新生成：

- 模型 intercept 从 `-44.990s` 调整为 `-44.390s`，slope 不变。
- 校准后 cue 800 落在 `3297.31s`。
- 这是人工目测校准，不是拟合结果；0.6s 可能随片段略有变化，模型 RMSE 仍为 1.084s。

### 片头是另一版剪辑

抽 0–120s 音频后确认：

- 视频 0–50s 是旁白开场："If I asked you what the Impressionists were best known for..."
- 字幕 8–38s 是**歌曲开场**（"And it hardly looked like a novel at all..."），与视频音频内容不同。
- 字幕 51.54s 的 "If I asked you" 才对应视频 0s 的旁白；片头三分句的偏移约为 -51.5 / -50.8 / -46.8s，并非常数。

因此片头前 ~50s 无法用统一偏移对齐；当前实现把负起点的 cue 夹紧到 0 并保留时长，写 `WARN_CLAMPED`。正文从 ~60s 起线性模型吻合。

### 发现并修复的问题

1. **高置信行直接用原始锚点偏移**：离群锚点（如 -58.7s）被写进字幕，导致同一段内跳动。修复为所有行统一使用拟合模型预测；锚点只参与拟合与置信度统计。
2. **全局不重叠推移**导致级联：ASS 本身有大量同时刻的排版事件，按文件顺序推移会把旁白一路推到 30s。修复为保留原始时长与间隔；只对负起点做夹紧。
3. 夹紧时保留原时长，而不是压成 1ms；新增 `WARN_CLAMPED`。

### 结论

- 正文的线性漂移已被正确识别；局部抽检误差约 0.1–2.6s。
- 模型 RMSE 1.084s，**G1 的 0.1s 中位数/P90 目标尚未达成**。
- 片头是另一版剪辑，属于不可对齐内容，应单独处理或人工跳过。
- 下一步优先级：局部分段模型（片头/剪辑断点）、更干净的锚点筛选、人工标注 300 行做正式 G1 评估。

首次运行（修复前）产物保留为 `S01E02.report.before-model-fix.json` 与 `S01E02.fixed.before-model-fix.ass`。

## 实验 2：E01 Gang of Four

| 字段 | 内容 |
| --- | --- |
| 影片 / 字幕 | `S01E01.Gang.of.Four...mkv`；`...简体&英文.ass`（UTF-16，920 个 cue，中英双语） |
| 模型 | whisper.cpp large-v3-turbo |
| 选中模型 | `linear`：intercept `-0.614s`（已含 `--shift 0.6`），slope `0.004450`（约 0.445% 漂移） |
| 覆盖率 | 96.7%（high 890 / medium 8 / low 22） |
| 模型 RMSE | 0.871s |
| 夹紧 | 2 个片头 cue |
| 输出 | 片源目录 `...简体&英文.校对.ass`；报告 `.local/experiments/impressionists/S01E01.report.json` |

说明：

- E01 字幕起点接近 0，不像 E02 有约 -45s 的起点偏移；但两集的漂移斜率接近（0.445% vs 0.454%），说明同一字幕组/片源存在一致的帧率或时间轴约定问题。
- E01 继承了 E02 的 `--shift 0.6` 人工校准；如果 E01 观看后仍有固定偏差，可单独调整。
- 1700s 处抽检：输出 cue 比 ASR 段落起点约早 0.5–1s，处于模型 RMSE 0.871s 的范围内；仍需人工观看确认。
- 输出保真：920 个 cue 中 917 个改写时间码，非时间字段 0 处变化，UTF-16 保持。

## 实验 3：Patagonia E01–E03

| 集数 | 模型 | 分段数 | RMSE | 覆盖率 | 输出 |
| --- | --- | --- | --- | --- | --- |
| E01 | piecewise | 18 | 2.010s | 91.2% | `帕塔哥尼亚：神秘天堂.E01.校对.srt` |
| E02 | linear | 1 | 1.386s | 99.4% | `帕塔哥尼亚：神秘天堂.E02.校对.srt` |
| E03 | linear | 1 | 0.455s | 85.1% | `帕塔哥尼亚：神秘天堂.E03.校对.srt` |

1800–1920s 逐词抽查（cue start 与 ASR 词起点之差）：

- **E01**：多数在 -0.9s 到 +0.3s；一个 +2.6s 离群。
- **E02**：连续多个 cue 约 **-1.1s**（输出偏早约 1s），另有少数离群；需要人工确认是否加 +1s 校准。
- **E03**：多数在 ±0.3s；少数 ASR 段落边界处离群。

文本与行数：三集均 100% 保留，所有 cue 的时间码均被改写。

### 本轮修复

1. **零时长 token**：whisper.cpp 对部分词输出 `start == end`，适配器原先丢弃；现在保留并给 10ms 最小时长。这是 E01 最初 RMSE 18s 的主因。
2. **线性模型选择**：去掉“斜率显著性”硬门槛，改为按 RMSE 改进选择；E02/E03 因此从 constant（RMSE 6.9/8.7）切换为 linear（1.386/0.455）。
3. **鲁棒分段**：局部中位数 + 变点，剔除离群锚点后再分段；E01 由 linear（6.748）改为 18 段 piecewise（2.010）。
4. 每集额外输出 `<report>.anchors.json`，用于逐条复核锚点。
