---
type: tasks
status: In Progress
owner: dream-365
depends_on: []
spec: ./spec.md
spec_sha256: "4247f9bc582cd48619f42beed2d6ebed3892e65c92fc22f7592e8e8dee25c7e7"
updated_at: 2026-11-05
---

# SubAlign 字幕时间轴音频对齐 执行拆解

| ID | 任务 | 覆盖 | 依赖 | 写入 | 完成标准 | 验证 |
| --- | --- | --- | --- | --- | --- | --- |
| T1 | CLI 骨架与参数校验 | G4 | — | src/subalign/cli.py | 非法参数返回退出码 1 且不创建输出；`--dry-run` 不写字幕；`--out` 与输入同路径、或扩展名与输入格式不一致被拒绝 | python -m pytest tests/test_cli.py -k contract |
| T2 | 媒体探测与音轨归一化 | G5 | T1 | src/subalign/media/ | fixture 视频产出 16kHz / 单声道 / `pcm_s16le` WAV（ffprobe 断言）；44.1kHz 立体声输入被重编码或返回 `ERR_MEDIA_FORMAT`；无音轨视频返回 `ERR_NO_AUDIO`；临时文件在成功与失败路径都被清理 | python -m pytest tests/test_media.py |
| T3 | SRT/ASS 解析、编码探测、文本归一化与语言标注 | G3 | T1 | src/subalign/subtitle/ | SRT 与 ASS 解析后写回，文本逐字一致、行序不变；ASS 非时间字段逐字节不变；UTF-8 BOM/GB18030 fixture 通过；每行产出 zh/en/mixed 标签；坏格式返回带行号的 `ERR_SUBTITLE_PARSE` | python -m pytest tests/test_subtitle.py |
| T11 | 双语分组与锚点行选择 | G1 | T3 | src/subalign/subtitle/bilingual/ | 时间重叠 ≥80% 的中英两行归组；锚点行语言与 ASR 语言一致；组内各行使用同一 delta；无匹配时整组 low-confidence | python -m pytest tests/test_bilingual.py |
| T4 | whisper.cpp 适配层（DTW token 时间戳） | G1 | T2 | src/subalign/asr/ | 对 60s fixture 输出按时间排序的 token 流与检测语言，字段满足 4.3；DTW 未启用时在报告标注；模型不可用时返回 `ERR_ASR_FAILED` | python -m pytest tests/test_asr.py -m slow |
| T5 | 锚点对齐 | G1 | T3, T4, T11 | src/subalign/align/ | 每个锚点行或双语组产出锚点或显式 low-confidence；`matched_ratio` 与 `confidence` 写入中间结果；空 token 流不抛错 | python -m pytest tests/test_align.py |
| T6 | 偏移模型选择与断点检测 | G2 | T5 | src/subalign/fit/ | 三类合成残差分别选中 constant、linear、piecewise；注入断点位置误差 ≤ 2 行；不稳定断点返回 `ERR_AMBIGUOUS_FIT` | python -m pytest tests/test_fit.py |
| T7 | SRT/ASS 原子写回与 JSON 报告 | G4 | T5 | src/subalign/io/, src/subalign/report/ | 输入 SHA-256 不变；SRT/ASS 均可写回；ASS 仅 `Start`/`End` 变化；报告通过 Schema（含 format/group_id/anchor_lang）；写入中断后只留临时文件 | python -m pytest tests/test_io.py |
| T8 | 回归 fixture 与精度评估脚本 | G1, G3 | T3, T6, T11 | tests/fixtures/, eval/ | 8 个 fixture（SRT/ASS，含 4 个双语）的模型类型与位移满足 G3；ASS 非时间字段不变；评估脚本按格式与语言输出中位数/P90 | python eval/precision.py --fixtures tests/fixtures |
| T9 | 端到端性能基准 | G5 | T2, T6, T7 | benchmarks/ | 100 分钟样例的耗时与峰值 RSS 写入 `benchmarks/latest.json`，字段含版本与模型名 | benchmarks/run.sh |
| T10 | 验证实验与基线对比 | G1, G2 | T8, T9 | docs/experiments/ | 《印象派》与双语 ASS 样本、注入断点、ffsubsync/alass 基线四份报告齐全，每份给出结论与未达项 | docs/experiments/README.md |
