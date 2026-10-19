# 所得的图标

开口的冷白弧是所想，弧口里的暖象牙珍珠是所得，底是午夜圆角方。

- `appicon.svg`：应用图标。`scripts/make-icon.py` 把它画成 `../AppIcon.icns`、`docs/logo.png`、`shell/ui/icon.png` 和 `shell/src-tauri/icons`。
- `menubar.svg` 与 `tray.svg`：菜单栏和托盘用的同一枚标记，笔画更粗，缩到很小仍看得清。
- `tray-dim.svg`：索引时金属弧变暗。Mac 的 `StatusIcon` 和 shell 的 `tray_icon.rs` 从顶部顺时针把亮色扫回来。
- `tray-paused.svg`：暂停时珍珠的位置换成两道竖条。
- 有更新时，右上角的圆点是程序画上去的，不在这些图里。
- `AppIcon.icon`：同一设计的 Icon Composer 稿（午夜底 + 弧与珍珠）。`build.sh` 用 `actool` 编进 `Assets.car`。

重新生成全部位图：

```sh
python3 scripts/make-icon.py
```

颜色：午夜 `#10162A`；冷白弧 `#F7F9FC`；暖象牙珍珠 `#F6E6C8`。不要用 DigUp 的四色块，也不要用它的绿和琥珀。
