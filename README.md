# exp-mobile-ui-layout-check

Android 计算器 UI 布局自动化测试 demo（Python + Maestro + OpenCV）。

## 环境准备

1. 安装 Python 3.10+
2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
3. 安装并配置 Maestro CLI
4. 确保 Android 设备已连接（`adb devices` 可见设备）

## 运行方式

### 真机/模拟器运行（Maestro + OpenCV）

```bash
python calculator_layout_demo.py \
  --app-id com.google.android.calculator \
  --flow-file maestro/calculator_layout_demo.yaml \
  --screenshot artifacts/calculator_screen.png
```

流程：
- Maestro 打开 Android 计算器应用并校验关键元素（`0`、`=`）可见
- Python 调用 ADB 截图
- OpenCV 检测按键区域并验证布局（至少 4 列、4 行、16 个按钮区域）

### 本地算法自检（无需设备）

```bash
python calculator_layout_demo.py --self-test
```
