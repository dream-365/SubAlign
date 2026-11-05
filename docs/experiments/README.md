# 验证实验

本目录存放 G1–G3 的真实验证记录。代码与单元测试已覆盖管线行为；下面的实验回答「0.1s 精度在真实片源上是否成立」。

## 前置条件

- 可用的 `ffmpeg` / `ffprobe`（见仓库根 `README.md` 的工具链说明）。
- 一个 GGML 模型，例如 `~/.cache/whisper/ggml-large-v3-turbo.bin`。
- 对比基线工具（用于 G2）：
  - `alass-cli` ≥ 2.0.0：`brew install alass`（可执行文件名为 `alass-cli`）
  - `ffsubsync` ≥ 0.5.1：`uv tool install --python 3.12 ffsubsync`
    （ffsubsync 依赖 numpy/scipy，Python 3.15 可能没有可用轮子；用 3.12 隔离安装）
  - 验证：`alass-cli --version`、`ffsubsync --version`
- 一部字幕错位的真实影片与对应字幕文件。首轮用纪录片《印象派》。

## 实验 1：单点验证（《印象派》）

目的：确认分段跳变能被自动识别，且逐行偏差可复核。

```bash
.venv/bin/python -m subalign align \
  --video "/path/to/impressionists.mp4" \
  --subtitle "/path/to/impressionists.ass" \
  --out ".local/experiments/impressionists.fixed.ass" \
  --report ".local/experiments/impressionists.report.json" \
  --model large-v3-turbo
```

记录：

- `model.kind` 是否为 `piecewise`，断点数量与位置。
- `coverage` 与 `warnings`。
- 人工抽查 30 行：`final_start` 与画面是否一致；偏差是否 ≤ 0.1s。
- 原字幕 SHA-256 是否不变。

## 实验 2：注入断点

目的：在可控数据上验证断点位置误差 ≤ 2 行。

1. 取一份已对齐的 SRT/ASS。
2. 在已知位置插入 10 个 ≥1.5s 的偏移段，生成 `injected.srt`。
3. 用同一影片跑 `subalign`。
4. 对比报告中的 `model.breakpoints` 与注入位置，记录召回与位置误差。

## 实验 3：基线对比

目的：验证 G2 的「P90 不劣于 ffsubsync/alass」。

```bash
# 本机 ffmpeg-full 依赖 ~/.local/lib 的 whisper.cpp 动态库
export DYLD_LIBRARY_PATH="$HOME/.local/lib"

# ffsubsync（启用 split 模式）
ffsubsync video.mp4 -i subtitle.srt -o ffsubsync.srt --split-penalty 10
# 若报 "Unable to detect speech"，改用：
# ffsubsync video.mp4 -i subtitle.srt -o ffsubsync.srt --vad auditok

# alass
alass-cli video.mp4 subtitle.srt alass.srt

# 本工具
.venv/bin/python -m subalign align --video video.mp4 --subtitle subtitle.srt \
  --out subalign.srt --model large-v3-turbo
```

> ffsubsync 默认 VAD 在短音频或纯 TTS 上可能检测不到语音；真实影片通常没问题，失败时用 `--vad auditok`。

用人工基准或同一份 truth 对比三份输出的起始/结束误差：

```bash
.venv/bin/python eval/precision.py --truth truth.srt --pred ffsubsync.srt
.venv/bin/python eval/precision.py --truth truth.srt --pred alass.srt
.venv/bin/python eval/precision.py --truth truth.srt --pred subalign.srt
```

## 结果记录

每个实验在 `docs/experiments/results.md` 追加一节，至少包含：

| 字段 | 内容 |
| --- | --- |
| 影片 / 字幕 | 片名、片源、字幕来源 |
| 格式 / 语言 | SRT 或 ASS；单语或中英双语 |
| 模型 | GGML 模型名与 SHA-256（报告中 `tool_versions`） |
| 选中模型 | constant / linear / piecewise |
| 覆盖率 | `coverage` |
| 起始误差 | 中位数 / P90 / 最大值 |
| 结束误差 | 中位数 / P90 / 最大值 |
| 断点 | 数量、位置、人工判定 |
| 结论 | 是否达到 G1/G2/G3；未达项与下一步 |

## 当前状态

代码与 53 个单元测试已通过；真实 whisper.cpp 慢测试通过；8 个 SRT/ASS fixture 的零位移写回逐字节一致。实验 1–3 尚待接入真实影片与基线工具，结果未填写。
