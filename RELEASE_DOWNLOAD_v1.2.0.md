# Cadence Interactive BOM v1.2.0 下载与使用说明

## 先看这个

如果你是第一次打开 GitHub，不知道该下载哪个文件，直接下载：

- `cadence-ibom-v1.2.0-delivery.zip`

这个就是给同事直接使用的完整包。  
下载后解压，双击 `CadenceInteractiveBOM.exe` 就可以。

## 推荐下载

如果你只是想直接使用工具，不需要看源码，建议下载以下文件之一：

- `cadence-ibom-v1.2.0-delivery.zip`
  - 完整交付包
  - 包含可执行版、使用说明、示例输出、输入文件目录
  - 适合同事直接解压后使用

- `cadence-ibom-v1.2.0-exe-only.zip`
  - 仅包含可执行版
  - 适合已经了解工具、只需要最小运行包的用户

## 最简使用步骤

1. 解压压缩包
2. 双击运行 `CadenceInteractiveBOM.exe`
3. 选择：
   - `BOM.xlsx`
   - `IPC-2581.xml`
4. 点击 `检查输入`，确认识别正常
5. 点击 `生成 HTML`
6. 打开生成的页面开始使用

## 输入文件要求

最少需要两份文件：

- `BOM.xlsx`
- `IPC-2581.xml`

可选：

- `Placement` 文件  
  只有在个别项目中，`IPC-2581` 坐标信息不足时才需要额外提供

## 你会得到什么

生成结果通常包括：

- `*.html`
  - 交互式 BOM 页面
- `*_report.txt`
  - 导入与生成摘要
- `*_inspect.txt`
  - 检查输入结果
- `*_error.log`
  - 仅生成失败时出现

## 使用特点

- 不需要安装 Python
- 支持中文/英文 BOM 表头识别
- 支持板框、器件几何显示和 BOM 联动
- 支持搜索、标记完成、仅看当前 BOM
- 支持导出当前结果为 `CSV / XLSX`

## 如果 BOM 表头识别不对

可执行版目录下有可编辑映射文件：

- `field_mapping.json`

如需适配公司内部自定义表头，请优先修改这份文件。  
不要修改 `_internal` 目录里的同名文件。

## 推荐给同事的下载建议

如果是第一次使用，优先下载：

- `cadence-ibom-v1.2.0-delivery.zip`

如果已经熟悉工具，只想拿到程序本体，下载：

- `cadence-ibom-v1.2.0-exe-only.zip`
