# SubAlign

以视频音轨为基准，校正 SRT/ASS 字幕的时间轴。识别层使用 whisper.cpp 的 DTW token 时间戳，对齐层用字幕文本做行级锚点，拟合层在常量、线性、分段常量三类偏移模型之间自动选择。

Spec 与执行拆解见：

- `docs/specs/SPEC-001-subtitle-timeline-alignment/spec.md`
- `docs/specs/SPEC-001-subtitle-timeline-alignment/tasks.md`
- `docs/architecture/system.md`

## 安装

```bash
python3 -m venv .venv
.venv/bin/pip install -e .
```

## 使用

```bash
.venv/bin/python -m subalign align \
  --video movie.mp4 \
  --subtitle movie.ass \
  --out movie.fixed.ass \
  --lang auto \
  --model large-v3-turbo \
  --report movie.fixed.report.json
```

- 默认模型是 `large-v3-turbo`；`large-v3` 仍可用 `--model large-v3` 显式指定。
- 输出格式跟随输入扩展名；不支持 SRT↔ASS 转换。
- 原文件只读；`--out` 必须是不存在的路径，或加 `--force`。
- `--dry-run` 只产出报告，不写字幕。
- ASS 只重写 `Dialogue` 的 `Start`/`End`，样式、定位、注释与编码/换行保持不变。
- 中英双语字幕按 ASR 语言选锚点行，译文行跟随同一修正量。

## 本地配置

敏感路径不写入仓库。复制 `.env.local.example` 为 `.env.local` 并填写本机路径：

```bash
cp .env.local.example .env.local
# 编辑 .env.local 后，按需 source 使用
source .env.local
```

- `WHISPER_MODEL_DIR`：GGML 模型目录，工具会读取。
- `MEDIA_ROOT`：实验用媒体根目录，供 runbook 中的命令使用。
- `.env.local` 与 `.local/`（本地实验产物）都已在 `.gitignore` 中。

## 工具链

- Python ≥ 3.11
- `whisper-cli`（whisper.cpp），模型放在 `~/.cache/whisper/` 或 `models/`
- `ffmpeg` / `ffprobe` ≥ 6.0
- 基线对比工具（仅实验用，可选）：
  - `alass-cli` ≥ 2.0.0：`brew install alass`（可执行文件名为 `alass-cli`）
  - `ffsubsync` ≥ 0.5.1：`uv tool install --python 3.12 ffsubsync`
    （ffsubsync 依赖 numpy/scipy，用 Python 3.12 安装最稳；不要装进项目的 3.15 venv）
  - 本机运行基线工具前需要 `export DYLD_LIBRARY_PATH="$HOME/.local/lib"`，因为它们会调用 `ffprobe`。

媒体层会自动在 `~/.local/lib` 存在 whisper.cpp 动态库时补 `DYLD_LIBRARY_PATH`，因此本机的 `ffmpeg-full` 可以直接使用。如果换机器后仍然缺库：

```bash
brew install whisper.cpp rubberband
# 或
brew reinstall ffmpeg
```

也可以用 `FFMPEG_BIN` / `FFPROBE_BIN` 指向一个可用的 ffmpeg。媒体层会固定输出 16kHz / 单声道 / PCM `s16le` WAV，并用 ffprobe 校验；不符合契约会返回 `ERR_MEDIA_FORMAT`。

## 测试

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m pytest -q -m slow   # 真实 whisper.cpp + say 合成语音
.venv/bin/python eval/precision.py --fixtures tests/fixtures/eval
```

## 已知边界

- 卡拉OK逐字标签、矢量绘图动画的时间重算不在首版范围。
- 中英以外语言可运行，但不承诺 0.1s 精度。
- `0.1s` 是实验目标；whisper.cpp 的 token 边界误差需要实测，不达标时先加强行级拟合与插值。
