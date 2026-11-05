# Benchmarks

`run.sh` 对给定视频跑完整管线，并把耗时与峰值 RSS 写入 `latest.json`。

```bash
benchmarks/run.sh /path/to/movie.mp4 /path/to/movie.srt ./movie.fixed.srt
```

- 模型默认 `large-v3-turbo`，可用 `SUBALIGN_MODEL=large-v3 benchmarks/run.sh ...` 覆盖。
- 计时用 `/usr/bin/time -l`，`latest.json` 包含 `real_seconds` 与 `max_rss_bytes`。

## 已记录

5 秒合成视频 + 单行中文字幕 + `ggml-large-v3-turbo`：

```json
{
  "real_seconds": 6.66,
  "max_rss_bytes": 1842855936
}
```

该结果包含模型加载，不能外推到 100 分钟正片。G5 的 100 分钟指标仍需用真实长片跑一次并记录。
