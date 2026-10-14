import type { SteleItem } from '../types/stele';
export const CORE_STELES = [
  { id: 'tang-duobao', recordId: 'tang_01_duobao', label: '唐·多宝塔感应碑', era: '唐天宝十一载', year: 752 },
  { id: 'han-caoquan', recordId: 'han_01_caoquan', label: '东汉·郃阳令曹全碑', era: '东汉中平二年', year: 185 },
  { id: 'wei-yuanhuai', recordId: 'wei-yuanhuai', label: '北魏·广平王元怀墓志铭', era: '北魏熙平二年', year: 517 },
  { id: 'wei-jianyi', recordId: 'wei-jianyi', label: '北魏·建义元年重度风化墓志', era: '北魏建义元年', year: 528 },
] as const;
export function resolveCoreId(id: string) { return CORE_STELES.find(c => c.id === id || c.recordId === id)?.id; }
// Two core algorithm samples exist outside the 28 museum records. Never alias Yuan Huai to Wu Gaoli,
// or assert that the synthetic Jianyi image is the museum's Wang Song rubbing.
export function graphSelectionItems(records: SteleItem[]): SteleItem[] {
  return CORE_STELES.map(c => {
    const existing = records.find(r => r.id === c.recordId);
    if (existing) return existing;
    const image = c.id === 'wei-yuanhuai' ? '/assets/stele/rubbings/stele_wei_yuanhuai.png' : '/assets/stele/rubbings/stele_wei_jianyi_fragment.png';
    return { id: c.id, title: c.id === 'wei-jianyi' ? '北魏碑拓数字化退化测试样本' : '广平王元怀墓志铭', dynasty: '北魏', author: '待考', script_type: '楷书',
      year: c.era, ganzhi: '', location: '待考', museum: '来源链待核', dimensions: '待考', summary: '核心算法样本；不借用其他馆藏记录。', historical_context: '', badges: ['身份待核'], weathering_level: '待评估',
      raw_image: image, clean_image: image, damaged_image: image, isDemo: true,
      metrics: { psnr: 0, ssim: 0, snr_gain: 0, glyph_completeness: 0, character_accuracy: 0 }, translation: '' } as SteleItem;
  });
}
