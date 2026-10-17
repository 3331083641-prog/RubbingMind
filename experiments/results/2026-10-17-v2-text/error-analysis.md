# 逐退化误差分析

各组7件文物；同碑两档强度不作为独立文物。置信区间按文物配对差值重采样。

| 分组 | 退化 | 方法 | PSNR | SSIM | 相对输入ΔdB | 95%聚类区间 | 劣于输入数 |
|---|---|---|---:|---:|---:|---|---:|
|development|gaussian|degraded|23.866|0.708|0.000|0.000, 0.000|0/14|
|development|gaussian|notch|23.764|0.706|-0.102|-0.296, -0.003|12/14|
|development|gaussian|joint|19.062|0.612|-4.804|-7.028, -2.332|12/14|
|development|gaussian|adaptive_joint|25.848|0.787|1.982|0.208, 3.871|2/14|
|development|salt_pepper|degraded|19.771|0.684|0.000|0.000, 0.000|0/14|
|development|salt_pepper|notch|19.766|0.682|-0.005|-0.025, 0.006|1/14|
|development|salt_pepper|joint|18.827|0.588|-0.944|-3.433, 1.636|9/14|
|development|salt_pepper|adaptive_joint|25.290|0.830|5.519|3.305, 8.201|1/14|
|development|periodic|degraded|23.280|0.687|0.000|0.000, 0.000|0/14|
|development|periodic|notch|36.741|0.974|13.462|10.947, 15.593|0/14|
|development|periodic|joint|15.529|0.362|-7.750|-8.668, -6.789|14/14|
|development|periodic|adaptive_joint|28.102|0.763|4.822|1.732, 8.121|2/14|
|development|blur|degraded|21.822|0.599|0.000|0.000, 0.000|0/14|
|development|blur|notch|21.779|0.598|-0.042|-0.130, 0.002|4/14|
|development|blur|joint|18.142|0.496|-3.680|-5.303, -2.468|14/14|
|development|blur|adaptive_joint|21.822|0.599|0.000|0.000, 0.000|0/14|
|development|occlusion|degraded|38.503|0.986|0.000|0.000, 0.000|0/14|
|development|occlusion|notch|36.812|0.975|-1.691|-4.423, -0.071|14/14|
|development|occlusion|joint|19.303|0.609|-19.201|-21.791, -16.619|14/14|
|development|occlusion|adaptive_joint|34.736|0.930|-3.768|-6.430, -1.438|12/14|
|test|gaussian|degraded|23.923|0.664|0.000|0.000, 0.000|0/14|
|test|gaussian|notch|23.795|0.661|-0.128|-0.371, -0.006|12/14|
|test|gaussian|joint|20.118|0.564|-3.805|-6.133, -1.425|11/14|
|test|gaussian|adaptive_joint|26.492|0.749|2.569|1.134, 4.088|2/14|
|test|salt_pepper|degraded|19.487|0.646|0.000|0.000, 0.000|0/14|
|test|salt_pepper|notch|19.485|0.644|-0.002|-0.018, 0.007|1/14|
|test|salt_pepper|joint|19.783|0.545|0.296|-1.727, 2.447|7/14|
|test|salt_pepper|adaptive_joint|26.152|0.845|6.666|4.702, 8.631|0/14|
|test|periodic|degraded|23.301|0.638|0.000|0.000, 0.000|0/14|
|test|periodic|notch|36.973|0.973|13.672|10.689, 16.242|0/14|
|test|periodic|joint|15.349|0.295|-7.952|-9.022, -6.871|14/14|
|test|periodic|adaptive_joint|27.386|0.714|4.085|1.680, 6.722|3/14|
|test|blur|degraded|21.459|0.585|0.000|0.000, 0.000|0/14|
|test|blur|notch|21.270|0.578|-0.189|-0.560, 0.001|6/14|
|test|blur|joint|18.531|0.462|-2.928|-3.381, -2.534|14/14|
|test|blur|adaptive_joint|21.459|0.585|0.000|0.000, 0.000|0/14|
|test|occlusion|degraded|35.354|0.985|0.000|0.000, 0.000|0/14|
|test|occlusion|notch|34.739|0.977|-0.614|-1.633, -0.070|14/14|
|test|occlusion|joint|20.366|0.559|-14.987|-17.029, -13.030|14/14|
|test|occlusion|adaptive_joint|32.500|0.919|-2.854|-4.755, -1.264|11/14|

## 解释与失败边界

- 固定联合对照没有接收退化标签；旧2026-10-15批次joint使用标签选陷波，有先验泄漏，两批均值不能直接解释为同一协议下的前后提升。
- 低通削弱高频噪声也削弱字口；形态学开运算会去掉比核更细的明亮笔画。CLAHE与锐化改变局部亮度并放大石花，可降低像素PSNR，即使视觉对比更强。
- 本批次自适应测试集的SSIM均值高于输入，但仍有负提升个例，且未全面优于每个对照；不能宣布普遍优越。
- 周期法在无周期输入上可能误检碑文排布本身的谱峰。保真门控只检查副作用风险，无法证明缺失历史字形恢复正确。
- 模糊和局部遮挡不等于噪声，保留原图常比强增强更忠实；遮挡区域没有信息恢复。对原有石花作NLM也可能远离实验参考图。
- 中心裁切未剔除空白或不利区域，七朝代各两件不是代表性随机样本，区间不能外推全体碑刻。
- 本次未依据测试组结果调整阈值；后续若继续调参，应另设未使用的文物留出集。
- 未训练OCR，未建立独立人工字形标签，不报告字符识别率。
