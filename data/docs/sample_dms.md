# DMS 疲劳检测夜间红外误报排障指南

**项目**：DMS（驾驶员监测系统）  
**场景**：夜间红外摄像头在弱光/逆光环境下触发疲劳/分心误报  
**文档版本**：v1.2  
**适用平台**：车载 DMS 算法模块（ARM Cortex-A55 / 高通 SA8155P 等）

---

## 一、现象描述

在夜间行驶场景中，DMS 系统出现以下典型误报问题：

1. **疲劳误报**：驾驶员精神状态正常，但系统持续触发"疲劳预警"或"闭眼超时"告警（PERCLOS 指标异常偏高）。
2. **分心误报**：驾驶员注视前方道路，但 HeadPose 估计偏差导致"注意力分散"告警。
3. **眼部特征丢失**：红外 LED 补光在强反射场景（如仪表盘反光、车窗玻璃反射路灯）下造成过曝，瞳孔检测置信度骤降（< 0.3）。
4. **抖动误报**：车辆经过减速带或颠簸路段时，人脸关键点跟踪抖动导致短暂误识别。

---

## 二、根本原因分析

### 2.1 红外曝光控制不足

夜间场景亮度变化范围极大（0.01 lux 至 5 lux）。若 ISP 自动曝光（AE）策略未针对近红外（850 nm / 940 nm）单独调参，会导致：

- **曝光过度**：LED 功率过高时瞳孔区域饱和，虹膜纹理消失，眼睛检测器误判为闭眼。
- **曝光不足**：LED 功率过低时人脸区域信噪比差，关键点定位误差 > 15 px。

### 2.2 模型训练数据分布偏差

若训练集中夜间红外样本比例不足（< 15%），模型在以下场景泛化能力差：

- 不同波段（850 nm vs 940 nm）的红外图像特征差异
- 戴眼镜场景（镜片对红外光的反射/折射）
- 深色皮肤与低反射率场景

### 2.3 时序滤波参数不合理

PERCLOS 计算基于滑动窗口（默认 60 秒），若窗口内偶发帧质量极差：

- 单帧误检可被放大累积，触发 PERCLOS 阈值（> 0.35）
- 未启用基于置信度的帧过滤（confidence-gated PERCLOS）

### 2.4 人脸跟踪丢失后冷启动

跟踪器（KCF/ByteTrack）在帧质量差时丢失目标，重新检测后：

- 短暂的关键点坐标跳变引发 HeadPose 异常
- 跟踪冷启动阶段约 5–10 帧数据质量不稳定

---

## 三、定位方法

### 3.1 数据采集与复现

```bash
# 1. 开启原始帧存储（需在配置文件中启用 debug_frame_dump）
dms_config set debug.frame_dump.enabled=true
dms_config set debug.frame_dump.path=/data/dms_debug/

# 2. 复现误报场景，收集 2–5 分钟原始 YUV/JPEG 帧
# 3. 导出告警日志
dms_log export --level WARN --output /data/dms_warn.log
```

### 3.2 关键指标核查

运行数据分析脚本，检查以下指标：

| 指标 | 正常范围 | 异常阈值 |
|------|----------|----------|
| 瞳孔检测置信度 | > 0.6 | < 0.3 |
| 人脸检测置信度 | > 0.7 | < 0.4 |
| 红外图像平均亮度 | 80–180（8 bit） | < 50 或 > 220 |
| PERCLOS 原始值（无滤波） | < 0.2 | > 0.4 |
| HeadPose Yaw 误差 | < 5° | > 15° |

```python
# 快速核查脚本示例
import dms_analyzer
report = dms_analyzer.analyze(frame_dir="/data/dms_debug/", log="/data/dms_warn.log")
print(report.summary())
```

### 3.3 ISP 曝光日志分析

```bash
# 查看 AE 收敛状态
grep "AE_STATUS\|LED_PWM\|GAIN" /data/dms_warn.log | tail -100
```

若发现 `LED_PWM > 85%` 且 `AE_STATUS=CONVERGED`，说明曝光过度，需调低 LED 功率上限。

---

## 四、解决方案

### 4.1 ISP 曝光参数调优（优先）

**步骤 1**：降低红外 LED 最大功率上限

```json
// dms_isp_config.json
{
  "ir_led": {
    "max_power_pct": 70,        // 从默认 100% 降至 70%
    "wavelength_nm": 940,
    "ae_target_mean": 120,      // 目标平均亮度
    "ae_roi": "face_region"     // 仅以人脸区域为 AE 参考区域
  }
}
```

**步骤 2**：启用置信度门控 PERCLOS

```json
// dms_algo_config.json
{
  "perclos": {
    "window_sec": 60,
    "fatigue_threshold": 0.35,
    "confidence_gate": 0.5,     // 置信度低于此值的帧不计入 PERCLOS
    "min_valid_frames_pct": 0.6 // 窗口内有效帧比例不足时不触发告警
  }
}
```

### 4.2 模型微调与数据增强

若调参无法完全解决问题，需补充训练数据：

1. **采集夜间真实样本**：在目标车型上收集不同驾驶员、不同行驶场景下的夜间红外数据，建议每类场景 ≥ 500 帧。
2. **数据增强策略**：
   - 随机亮度扰动（±30 灰度级）
   - 随机红外反射噪声模拟（镜面高光 patch）
   - 眼镜反射模拟（椭圆高光区域叠加）
3. **微调配置参考**：
   ```bash
   python train.py \
     --base-model dms_v2.3.onnx \
     --data-dir /data/night_ir_samples/ \
     --epochs 30 \
     --lr 1e-4 \
     --augment night_ir
   ```

### 4.3 时序后处理优化

- **增加跟踪稳定性判断**：跟踪冷启动后前 10 帧不纳入告警判断。
- **HeadPose 平滑滤波**：对 Yaw/Pitch/Roll 使用卡尔曼滤波（Q=0.01, R=0.1）。
- **告警防抖**：连续满足阈值 ≥ 3 次（约 300 ms）才触发告警，避免抖动误报。

### 4.4 验证方法

```bash
# 回归测试：在修改后的配置/模型上重跑复现帧
python eval_dms.py \
  --frame-dir /data/dms_debug/ \
  --config dms_isp_config.json \
  --model dms_v2.3_finetuned.onnx \
  --output /data/eval_report.json

# 检查误报率是否下降至目标（< 2%）
python check_report.py /data/eval_report.json --target-far 0.02
```

---

## 五、预防措施

1. **夜间红外测试用例纳入 CI**：每次模型更新后自动运行夜间场景回归测试。
2. **线上质量监控**：在量产车辆上收集匿名化的 DMS 置信度分布数据，若某批次夜间置信度中位数 < 0.5 则触发告警。
3. **灰度发布**：模型或参数更新通过 OTA 分批下发，首批 1% 车辆观测 72 小时，无异常后全量推送。
4. **文档更新**：每次排障后更新本文档，记录根因与解决方案版本对应关系。

---

## 六、相关文档与资源

- DMS 算法技术白皮书 v3.0（内部）
- ISP 调参手册（见硬件团队 Confluence）
- `dms_analyzer` 工具使用手册（`docs/tools/dms_analyzer.md`）
- 夜间红外测试数据集访问权限：联系数据平台团队申请
