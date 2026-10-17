"""Preserve negative results and compare methods within artifact clusters."""
import csv
import json
import statistics
import argparse
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
FOLDER=ROOT/'experiments/results/2026-10-17-v2'


def main():
    data=json.loads((FOLDER/'results.json').read_text('utf8'))
    rows=data['rows'];output=[]
    test_summary={r['method']:r for r in data['summary'] if r['split']=='test'}
    improved=test_summary['adaptive_joint']['ssimMean']>test_summary['degraded']['ssimMean']
    rng=np.random.default_rng(20261017)
    for split in ['development','test']:
        for mode in data['config']['degradations']:
            for method in data['config']['methods']:
                values=[r for r in rows if r['split']==split and r['method']==method and r['degradation']==mode]
                baseline={r['caseId']:r for r in rows if r['split']==split and r['method']=='degraded' and r['degradation']==mode}
                deltas={sid:statistics.mean(r['psnr']-baseline[r['caseId']]['psnr'] for r in values if r['sampleId']==sid) for sid in {r['sampleId'] for r in values}}
                groups=list(deltas.values());boot=rng.choice(groups,(2000,len(groups))).mean(1)
                output.append({'split':split,'degradation':mode,'method':method,'n':len(values),'artifactN':len(groups),
                    'psnrMean':statistics.mean(r['psnr'] for r in values),'ssimMean':statistics.mean(r['ssim'] for r in values),
                    'edgeF1Mean':statistics.mean(r['edgeF1'] for r in values),'processingMsMean':statistics.mean(r['processingMs'] for r in values),
                    'deltaPSNRvsInput':statistics.mean(groups),'deltaPSNRClusterCI95':np.percentile(boot,[2.5,97.5]).tolist(),
                    'worseThanInputN':sum(r['psnr']<baseline[r['caseId']]['psnr'] for r in values)})
    with (FOLDER/'by-degradation.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(output[0]));writer.writeheader();writer.writerows(output)
    lines=['# 逐退化误差分析','', '各组7件文物；同碑两档强度不作为独立文物。置信区间按文物配对差值重采样。',
           '', '| 分组 | 退化 | 方法 | PSNR | SSIM | 相对输入ΔdB | 95%聚类区间 | 劣于输入数 |','|---|---|---|---:|---:|---:|---|---:|']
    for r in output:
        if r['method'] in ('degraded','joint','adaptive_joint','notch'):
            lines.append(f"|{r['split']}|{r['degradation']}|{r['method']}|{r['psnrMean']:.3f}|{r['ssimMean']:.3f}|{r['deltaPSNRvsInput']:.3f}|{r['deltaPSNRClusterCI95'][0]:.3f}, {r['deltaPSNRClusterCI95'][1]:.3f}|{r['worseThanInputN']}/{r['n']}|")
    lines+=['','## 解释与失败边界','',
      '- 固定联合对照没有接收退化标签；旧2026-10-15批次joint使用标签选陷波，有先验泄漏，两批均值不能直接解释为同一协议下的前后提升。',
      '- 低通削弱高频噪声也削弱字口；形态学开运算会去掉比核更细的明亮笔画。CLAHE与锐化改变局部亮度并放大石花，可降低像素PSNR，即使视觉对比更强。',
      ('- 本批次自适应测试集的SSIM均值高于输入，但仍有负提升个例，且未全面优于每个对照；不能宣布普遍优越。' if improved else '- 本批次独立测试SSIM不优于输入，MAD/NLM、周期峰与孤立点启发式仍可能把真实细节当噪声；不能宣布普遍优越。'),
      '- 周期法在无周期输入上可能误检碑文排布本身的谱峰。保真门控只检查副作用风险，无法证明缺失历史字形恢复正确。',
      '- 模糊和局部遮挡不等于噪声，保留原图常比强增强更忠实；遮挡区域没有信息恢复。对原有石花作NLM也可能远离实验参考图。',
      '- 中心裁切未剔除空白或不利区域，七朝代各两件不是代表性随机样本，区间不能外推全体碑刻。',
      '- 本次未依据测试组结果调整阈值；后续若继续调参，应另设未使用的文物留出集。',
      '- 未训练OCR，未建立独立人工字形标签，不报告字符识别率。']
    (FOLDER/'error-analysis.md').write_text('\n'.join(lines)+'\n','utf8')
    old=json.loads((ROOT/'experiments/results/2026-10-15/results.json').read_text('utf8'))
    historical=[]
    for mode in old['config']['degradations']:
        for method in old['config']['methods']:
            vals=[r for r in old['rows'] if r['method']==method and r['degradation']==mode]
            historical.append({'degradation':mode,'method':method,'n':len(vals),'psnrMean':statistics.mean(r['psnr'] for r in vals),'ssimMean':statistics.mean(r['ssim'] for r in vals)})
    # Analysis is new; historical original files are not written.
    (FOLDER/'historical-by-degradation.json').write_text(json.dumps(historical,ensure_ascii=False,indent=2),'utf8')
    print('Wrote grouped error analysis; all negative cases retained.')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--folder',default='experiments/results/2026-10-17-v2');args=parser.parse_args()
    FOLDER=ROOT/args.folder
    main()
