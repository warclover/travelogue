# LCC V1 · 长图协作取消狗粮（2026-07-15）

| Studio | `http://127.0.0.1:8768` |
| Trip | `demo-815dc906d3` |

## 步骤与结果

- **SETUP**: ✅ HTTP 200
- **START**: ✅ status=202 body={'ok': True, 'jobId': 'job-cd5cb59d396d'}
- **MID-STATUS**: ✅ status=running hint='正在全页截图并采集切分边界…'
- **CANCEL**: ✅ http=200 body={'ok': True, 'status': 'cancelled', 'purged': False, 'purgedOutputs': True}
- **RESTART**: ✅ status=202 jobId=job-0d78c43ad5b3
- **FINAL**: ✅ status=cancelled result=None
- **UI-CTA**: ✅ showExporting 出现「取消导出」；无「无法取消」

**汇总**: 全部通过

