# Release Notes v1.2.0

发布日期：2026-05-28

## 概要

`v1.2.0` 是当前第一版可交付版本，重点完成了：

- Cadence / Allegro 导出数据的本地交互式 BOM 主流程
- `IPC-2581` 纯几何渲染
- 启动器与交付包整理
- 字段映射外置配置
- 可执行版打包

## 核心功能

- 读取 `BOM xlsx/csv/tsv/txt`
- 读取 `IPC-2581 xml`
- 可选读取 `Placement htm/html/xlsx/csv/tsv/txt`
- 从 `IPC-2581` 解析器件坐标、封装外形、板框
- 左侧 BOM 与右侧板视图双向联动
- 点击器件反定位 BOM
- 搜索、筛选、完成标记
- 右侧滚轮缩放、拖动和平移
- `仅当前 BOM` 视图
- 导出当前结果到 `CSV / XLSX`

## 启动器增强

- 最近项目记录
- 删除最近项目
- 自动记住上次输入
- 打开输出目录
- 打开最近页面 / 最近报告
- `检查输入` 预检
- 自动生成 `inspect / report / error log`
- 默认输出避免覆盖旧结果

## 数据适配

- 中文/英文 BOM 表头识别
- `field_mapping.json` 外置映射
- 测试点自动识别与剔除

## 打包与交付

- 提供 `PyInstaller` spec
- 提供 `exe` 可执行版
- 交付包已整理为可直接发同事的版本

## 已知边界

- 当前主流程以纯几何显示为主，不依赖板图
- 板框依赖 `IPC-2581` 中的 `Profile` 或 `01_OUTLINE`
- `field_mapping.json` 需要按实际公司 BOM 表头维护
