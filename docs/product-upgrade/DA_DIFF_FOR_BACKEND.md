# degradation_analysis.py：请架构后端签字的剩余 diff

- 作者：RM-评测科学家（Agent 04+05）
- 时间：见 git commit
- 范围：`git diff agent/arch-backend agent/eval-sci -- degradation_analysis.py`
- 说明：`change_stats` 的 int32 两边已一致（`4379827` / `530b45e`），不在本 diff 内。

```diff
@@ AdaptiveRubbingRestorer.restore（门控之后、return 之前）
+        change = change_stats(image, result)
+        if not gate['accepted']:
+            output_mode = 'gate_fallback_original'
+        elif change['isPassthrough']:
+            output_mode = 'identity_no_evidence'
+        else:
+            output_mode = 'processed'
         return result, {...,
-                        'selectedOutput':'candidate' if gate['accepted'] else 'original',
+                        'selectedOutput':'original' if change['isPassthrough'] else 'candidate',
+                        'outputMode':output_mode,'changeStats':change,
                         'limitations':...}

@@ AdaptiveRubbingRestorerV22.restore（平坦块早退）
                 'selectedOutput': 'original',
+                'outputMode': 'gate_fallback_original',
+                'changeStats': change_stats(image, image),
```

语义见 `REPORT_DATA_SPEC.md` §9（D-2 selectedOutput；D-3 两层 outputMode）。
