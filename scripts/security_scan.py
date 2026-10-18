# -*- coding: utf-8 -*-
"""
墨韵智考 - 仓库安全与敏感信息合规扫描脚本
用于在 Git Commit / CI 前排查 API 密钥、身份令牌、私有路径及敏感配置
"""
import os
import re
import sys

PATTERNS = [
    (re.compile(r"sk-[a-zA-Z0-9_-]{20,}"), "OpenAI / LLM API Key (sk-...)"),
    (re.compile(r"ghp_[a-zA-Z0-9]{30,}"), "GitHub Personal Access Token (ghp_...)"),
    (re.compile(r"gho_[a-zA-Z0-9]{30,}"), "GitHub OAuth Token (gho_...)"),
    (re.compile(r"-----BEGIN (RSA|EC|DSA|OPENSSH|PRIVATE) KEY-----"), "Private Key Block"),
    (re.compile(r"(?:api[_-]?key|secret_key|access_token|password)\s*[:=]\s*['\"][a-zA-Z0-9_\-]{16,}['\"]", re.IGNORECASE), "Generic Hardcoded Secret"),
    # Provenance SHA-256 values are not standalone telephone numbers.
    (re.compile(r"(?<![A-Za-z0-9.])[1-9]\d{10}(?![A-Za-z0-9.])"), "Phone Number (Possible 11-digit mobile)"),
]

IGNORED_DIRS = {
    "node_modules", "dist", ".vite", ".git", "__pycache__", ".pytest_cache", ".ruff_cache",
    ".gemini", "venv", ".venv", "runtime", "results"
}

IGNORED_FILES = {
    "security_scan.py", "package-lock.json"
}
TEXT_EXTENSIONS = {'.py', '.ts', '.tsx', '.js', '.json', '.md', '.txt', '.yaml', '.yml',
                   '.ps1', '.bat', '.toml', '.ini', '.css', '.html', '.sh', '.csv'}

def scan_repository(root_dir="."):
    findings = []
    print(f"[*] 开始扫描敏感信息与安全风险: {os.path.abspath(root_dir)}")
    
    file_count = 0
    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and not d.startswith('node_modules.partial-')]
        for f in files:
            if f in IGNORED_FILES or os.path.splitext(f)[1].lower() not in TEXT_EXTENSIONS:
                continue
            
            filepath = os.path.join(root, f)
            file_count += 1
            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as fp:
                    for line_idx, line in enumerate(fp, 1):
                        for pattern, desc in PATTERNS:
                            m = pattern.search(line)
                            if m:
                                # 忽略误报（如代码中的占位符、注释、公开链接、纯数字维度）
                                matched_str = m.group(0)
                                if "placeholder" in line.lower() or "your_" in line.lower() or "example" in line.lower():
                                    continue
                                if "Phone" in desc and (any(k in line for k in ["width", "height", "timestamp", "version", "seed", "size", "step", "color", "00000000", "http://", "https://"]) or "/" in line):
                                    continue
                                findings.append({
                                    "file": filepath,
                                    "line": line_idx,
                                    "desc": desc,
                                    "snippet": line.strip()[:100]
                                })
            except Exception as e:
                print(f"[!] 读取文件异常 {filepath}: {e}")

    print(f"[*] 扫描完成，共检测文本代码文件: {file_count} 个")
    if not findings:
        print("[OK] Security scan passed: No leaked API keys, tokens, or credentials found!")
        return 0
    else:
        print(f"[!] Found {len(findings)} potential security findings:")
        for f in findings:
            print(f"    - [{f['desc']}] {f['file']}:{f['line']} (content redacted)")
        return 1

if __name__ == "__main__":
    sys.exit(scan_repository("."))
