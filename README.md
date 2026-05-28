# cadence-ibom

`cadence-ibom` 是一个面向 `Cadence / Allegro` 的本地交互式 BOM 工具。  
它读取 `BOM`、`IPC-2581` 和可选 `Placement`，生成可离线打开的单文件 `HTML` 页面，用于器件定位、装配辅助、返修查找和物料核对。

## 同事下载入口

如果你只是想直接使用工具，不需要看源码，请不要下载仓库里的 `.py`、`.json`、`.spec` 文件。  
请直接进入 Release 页面下载压缩包：

- [v1.2.0 Release](https://github.com/Yuluoqianmo/cadence-ibom/releases/tag/v1.2.0)

推荐下载：

- `cadence-ibom-v1.2.0-delivery.zip`
  - 推荐第一次使用下载这个
  - 包含可执行版、使用说明、示例输出、输入文件目录

- `cadence-ibom-v1.2.0-exe-only.zip`
  - 只包含程序本体
  - 适合已经熟悉工具、只想拿到最小运行包的人

最简使用步骤：

1. 下载并解压 `cadence-ibom-v1.2.0-delivery.zip`
2. 双击运行 `CadenceInteractiveBOM.exe`
3. 选择：
   - `BOM.xlsx`
   - `IPC-2581.xml`
4. 点击 `检查输入`
5. 点击 `生成 HTML`

输入文件最少需要：

- `BOM.xlsx`
- `IPC-2581.xml`

说明：

- 普通同事只需要看 Release 和压缩包，不需要看下面的源码说明
- 如果你是开发者，下面的内容才和你有关

## 特性

- 支持 `BOM xlsx/csv/tsv/txt`
- 支持 `IPC-2581 xml`
- 可选支持 `Placement htm/html/xlsx/csv/tsv/txt`
- 支持中文/英文表头识别
- 支持外置字段映射配置
- 从 `IPC-2581` 读取器件坐标、封装几何和板框
- 左侧 BOM 与右侧视图双向联动
- 点击右侧器件反定位左侧 BOM
- 支持搜索、状态筛选、完成标记
- 支持滚轮缩放、拖动画布、复位视图
- 支持 `仅当前 BOM` 视图
- 支持导出当前结果到 `CSV / XLSX`
- 自动生成 `inspect / report / error log`

## 仓库结构

以下内容主要给开发或维护工具的人看：

- `generate_ibom.py`
  主生成脚本
- `ibom_launcher.py`
  图形启动器源码
- `field_mapping.json`
  BOM / Placement 字段映射配置
- `CadenceInteractiveBOM.spec`
  `PyInstaller` 打包配置
- `samples/`
  轻量示例输入

## 快速开始

### 脚本版

环境要求：

- Windows
- Python 3.10+

启动器：

```powershell
python .\ibom_launcher.py
```

命令行生成：

```powershell
python .\generate_ibom.py --bom .\samples\bom.tsv --placement .\samples\placement.csv --output .\dist\sample.html
```

### 打包 exe

```powershell
pyinstaller .\CadenceInteractiveBOM.spec
```

输出目录：

- `dist/CadenceInteractiveBOM/`

## 输入文件

最少输入：

- `BOM.xlsx`
- `IPC-2581.xml`

可选输入：

- `Placement` 文件

说明：

- 如果 `IPC-2581` 已包含完整器件坐标，则 `Placement` 可不提供
- 当前主流程以纯几何显示为主，不依赖板图

## 字段映射

字段映射文件：

- `field_mapping.json`

包含两类配置：

- `bom_aliases`
- `placement_aliases`

如果公司内部 BOM 表头有变化，优先修改这个文件，不需要直接改 Python 代码。

## 生成结果

生成 HTML 时，通常会得到：

- `*.html`
- `*_inspect.txt`
- `*_report.txt`
- `*_error.log`（仅失败时）

这些文件都带统一批次号，便于排查和归档。

## 不纳入仓库的内容

以下内容默认不提交：

- `dist/`
- `build/`
- `交付包_交互式BOM/`
- `用户输入文件放这里/`
- 真实项目 BOM / XML / PDF / PNG
- 生成的 `HTML / report / inspect / error log`
- 本地状态文件 `launcher_state.json`
