# 参与所得 (Suode)

所得是 [DigUp](https://github.com/ARahim3/DigUp) 的再品牌，原作版权归 Abdur Rahim，MIT。问题与拉取请求请发到本仓库 [xiaoou-waou/suosijisuode](https://github.com/xiaoou-waou/suosijisuode)。

Thanks for your interest in 所得. It's a small project, so a few notes up front save everyone time.

## Open an issue first

Please open an issue before you write any code, for a fix as much as for a feature. The same fix or feature may already
be in progress and not pushed yet. An issue gets you a clear "yes", "not now" or "here's how it should fit" before you
spend an evening on it. A pull request that arrives without one may be closed with a link back here.

## Pull requests

Once an issue says go:

- Keep it to one fix or one feature, with the reason in the description.
- Make sure `swift test` passes, and `cargo test` in `shell/src-tauri` if you change the Windows and Linux app.
- If it changes what search returns, run the evals in `evals/` before and after (see "Build from source" in the
  README) and include both results.
- For speed or memory changes, measure before and after on the same computer.

Suode keeps everything on your computer, so changes that send data elsewhere, like telemetry or cloud services, aren't a
fit.

## Where things are

The search engine in `Sources/SuodeKit` is the same Swift code on every system; what differs by system lives in its
`Platform/Apple` and `Platform/Portable` folders. The Mac app is `Sources/SuodeApp` (SwiftUI). The Windows and Linux
app is `shell/` (Tauri: Rust, with plain HTML and JavaScript for its windows), which runs the engine as a helper
program. `scripts/` builds llama.cpp, ffmpeg and the packages, and `.github/workflows/packages.yml` shows every step of
the Windows and Linux builds. "Build from source" in the README gets you started.

## What to expect

Suode is maintained alongside a day job and other projects, and most of the time it gets goes into the plan for where
it's headed, so replies can take a few days, sometimes longer. A quiet week means busy, not ignored, and every issue
gets an answer, even if it's "not now".

Not every pull request will be merged, even good ones. The project has a direction, and some changes won't fit it.
Others get reworked or rewritten to fit work in progress, and when that happens you'll be credited in the release
notes.

## Reporting a bug

Helpful reports include your computer (on a Mac its chip and memory; on Windows and Linux its processor and graphics
card), the system and Suode versions (on Linux also the desktop, like GNOME or KDE, and Wayland or X11), what you did
or searched for, and what you expected instead. Logs are in:

- Mac: `~/Library/Application Support/Suode/index.noindex` (`app.log` and `indexer.log`)
- Windows: `%LOCALAPPDATA%\com.xiaoou.suode\logs`, and `worker.log` in `%LOCALAPPDATA%\Suode\index`
- Linux: `~/.local/share/com.xiaoou.suode/logs`, and `worker.log` in `~/.local/share/suode/index`

They can contain file names and your searches, so look through them before you paste.

For a security problem, please use "Report a vulnerability" on the Security tab instead of a public issue.
