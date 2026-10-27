# 分析舞台交互

默认算法比较；点击证据图窗进入对应舞台。沿用 URL panel / method / sample / case / split / deg，新增指标状态也写入 URL。切换面板不重新获取批次结果；机制和测量原因按需读取并复用。

采用浏览器 Shared View Transition（支持时）实现缩略窗到舞台的空间连续性；不支持时用 transform / opacity 弹簧曲线进入。保留键盘可达的 tab、aria-selected、明确标题；布局稳定后 ResizeObserver 重绘 ECharts。

专注模式在页面内展开，ESC 恢复并回到触发按钮；筛选和案例不清空。减少动态效果、低性能设备及打印禁用进场／计数过渡，直接显示稳定真实值；null 显示未评测，永不转成 0。
