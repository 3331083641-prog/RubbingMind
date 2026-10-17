# 逐退化误差分析

各组7件文物；同碑两档强度不作为独立文物。置信区间按文物配对差值重采样。

| 分组 | 退化 | 方法 | PSNR | SSIM | 相对输入ΔdB | 95%聚类区间 | 劣于输入数 |
|---|---|---|---:|---:|---:|---|---:|
|development|gaussian|degraded|23.812|0.689|0.000|0.000, 0.000|0/14|
|development|gaussian|notch|23.804|0.689|-0.008|-0.011, -0.006|14/14|
|development|gaussian|joint|19.827|0.596|-3.985|-6.297, -1.494|12/14|
|development|gaussian|adaptive_joint|25.948|0.754|2.136|0.034, 4.313|3/14|
|development|salt_pepper|degraded|19.934|0.665|0.000|0.000, 0.000|0/14|
|development|salt_pepper|notch|19.938|0.666|0.004|0.003, 0.005|0/14|
|development|salt_pepper|joint|19.490|0.570|-0.444|-2.744, 1.953|8/14|
|development|salt_pepper|adaptive_joint|25.674|0.837|5.740|3.029, 8.655|0/14|
|development|periodic|degraded|23.254|0.667|0.000|0.000, 0.000|0/14|
|development|periodic|notch|38.164|0.984|14.910|13.970, 15.894|0/14|
|development|periodic|joint|15.667|0.336|-7.587|-8.510, -6.659|14/14|
|development|periodic|adaptive_joint|29.307|0.759|6.054|3.063, 9.046|3/14|
|development|blur|degraded|21.510|0.584|0.000|0.000, 0.000|0/14|
|development|blur|notch|21.511|0.584|0.001|0.001, 0.001|0/14|
|development|blur|joint|18.537|0.471|-2.973|-3.321, -2.659|14/14|
|development|blur|adaptive_joint|21.510|0.584|0.000|0.000, 0.000|0/14|
|development|occlusion|degraded|39.274|0.986|0.000|0.000, 0.000|0/14|
|development|occlusion|notch|39.095|0.985|-0.179|-0.328, -0.066|14/14|
|development|occlusion|joint|20.049|0.596|-19.225|-21.195, -17.352|14/14|
|development|occlusion|adaptive_joint|35.113|0.930|-4.161|-7.026, -1.129|8/14|
|test|gaussian|degraded|23.854|0.714|0.000|0.000, 0.000|0/14|
|test|gaussian|notch|23.727|0.712|-0.126|-0.368, -0.004|13/14|
|test|gaussian|joint|20.204|0.579|-3.649|-6.942, 0.189|10/14|
|test|gaussian|adaptive_joint|23.560|0.662|-0.293|-1.088, 0.373|3/14|
|test|salt_pepper|degraded|19.897|0.693|0.000|0.000, 0.000|0/14|
|test|salt_pepper|notch|19.887|0.690|-0.010|-0.038, 0.004|2/14|
|test|salt_pepper|joint|19.109|0.524|-0.788|-3.334, 2.093|10/14|
|test|salt_pepper|adaptive_joint|21.456|0.664|1.559|0.537, 2.995|1/14|
|test|periodic|degraded|23.259|0.693|0.000|0.000, 0.000|0/14|
|test|periodic|notch|37.637|0.983|14.377|11.057, 17.711|0/14|
|test|periodic|joint|15.669|0.331|-7.590|-8.605, -6.263|14/14|
|test|periodic|adaptive_joint|27.334|0.709|4.075|0.793, 7.563|4/14|
|test|blur|degraded|23.318|0.561|0.000|0.000, 0.000|0/14|
|test|blur|notch|23.244|0.559|-0.074|-0.222, 0.001|2/14|
|test|blur|joint|19.616|0.467|-3.702|-6.202, -2.087|14/14|
|test|blur|adaptive_joint|23.318|0.561|0.000|0.000, 0.000|0/14|
|test|occlusion|degraded|35.255|0.984|0.000|0.000, 0.000|0/14|
|test|occlusion|notch|32.235|0.972|-3.020|-9.030, -0.009|12/14|
|test|occlusion|joint|20.228|0.575|-15.027|-18.183, -11.530|14/14|
|test|occlusion|adaptive_joint|31.084|0.848|-4.172|-7.648, -1.040|10/14|

## 解释与失败边界

- 固定联合对照没有接收退化标签；旧2026-10-15批次joint使用标签选陷波，有先验泄漏，两批均值不能直接解释为同一协议下的前后提升。
- 低通削弱高频噪声也削弱字口；形态学开运算会去掉比核更细的明亮笔画。CLAHE与锐化改变局部亮度并放大石花，可降低像素PSNR，即使视觉对比更强。
- 新自适应方法开发组总体改善，但独立测试组SSIM不优于输入，说明MAD/NLM、周期峰启发式和孤立点判断仍会把真实细节当噪声。不能宣布普遍优越。
- 周期法在无周期输入上可能误检碑文排布本身的谱峰。保真门控只检查副作用风险，无法证明缺失历史字形恢复正确。
- 模糊和局部遮挡不等于噪声，保留原图常比强增强更忠实；遮挡区域没有信息恢复。对原有石花作NLM也可能远离实验参考图。
- 中心裁切未剔除空白或不利区域，七朝代各两件不是代表性随机样本，区间不能外推全体碑刻。
- 本次未依据测试组结果调整阈值；后续若继续调参，应另设未使用的文物留出集。
- 未训练OCR，未建立独立人工字形标签，不报告字符识别率。
