# cadence-ibom

一个面向 `Cadence / Allegro` 的本地交互式 BOM 工具源码仓库。  
工具读取 `BOM`、`IPC-2581` 和可选 `Placement`，生成一个可离线打开的单文件 `HTML` 页面，用于器件定位、装配辅助、返修查找和物料核对。

## 仓库内容

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

## 核心能力

- 导入 `BOM xlsx/csv/tsv/txt`
- 导入 `IPC-2581 xml`
- 可选导入 `Placement htm/html/xlsx/csv/tsv/txt`
- 中文/英文表头识别
- 字段映射外置配置
- 从 `IPC-2581` 读取器件坐标、封装几何和板框
- 左侧 BOM 与右侧视图双向联动
- 点击右侧器件反定位左侧 BOM
- 鼠标悬停器件显示 `RefDes / 值 / 型号 / 封装`
- `仅当前 BOM` 视图
- 搜索、状态筛选、完成标记
- 滚轮缩放、拖动画布、复位视图
- 导出 `CSV`
- 导出 `XLSX`
- 自动生成 `inspect / report / error log`

## 运行方式

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

打包输出目录：

- `dist/CadenceInteractiveBOM/`

## 字段映射

字段映射定义在：

- `field_mapping.json`

包含两类配置：

- `bom_aliases`
- `placement_aliases`

如果公司内部 BOM 表头有变化，优先修改这个文件，不需要直接改 Python 代码。

## 输入文件

最少输入：

- `BOM.xlsx`
- `IPC-2581.xml`

可选输入：

- `Placement` 文件

说明：

- 如果 `IPC-2581` 已包含完整器件坐标，则 `Placement` 可不提供
- 当前主流程以纯几何显示为主，不依赖板图

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
