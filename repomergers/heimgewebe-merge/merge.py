#!/usr/bin/env python3
from __future__ import annotations
import argparse, shutil, subprocess, sys, fnmatch, re
from pathlib import Path

# -------- utils --------
def sh(cmd: list[str], cwd: Path | None = None) -> str:
    return subprocess.check_output(cmd, cwd=str(cwd) if cwd else None, text=True).strip()

def want(path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(path, pat) for pat in patterns)

def looks_binary(p: Path, cutoff: int) -> bool:
    try:
        with p.open("rb") as f:
            chunk = f.read(min(cutoff, 8192))
        return b"\0" in chunk
    except Exception:
        return True

def human_bytes(num_bytes: int) -> str:
    value = float(num_bytes)
    for unit in ("B", "KiB", "MiB", "GiB"):
        if value < 1024 or unit == "GiB":
            return f"{value:.0f} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024

def append_with_split(parts_dir: Path, parts: list[Path], cur_size: int, max_bytes: int, text: str):
    if not parts:
        parts.append(parts_dir / "dossier-part-0001.md")
        parts[-1].write_text("", encoding="utf-8")
        cur_size = 0
    data = text.encode("utf-8")
    if cur_size + len(data) > max_bytes:
        idx = len(parts) + 1
        parts.append(parts_dir / f"dossier-part-{idx:04d}.md")
        parts[-1].write_text("", encoding="utf-8")
        cur_size = 0
    with parts[-1].open("a", encoding="utf-8") as f:
        f.write(text)
    return parts, cur_size + len(data)

# -------- main --------
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Merge heimgewebe org repos into split Markdown dossiers with crosslinks.")
    p.add_argument("--org", required=True)
    p.add_argument("--repos", nargs="+", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--max-bytes", type=int, default=5*1024*1024)
    p.add_argument("--globs", default="README.md,docs/**,**/*.md,**/*.rs,**/*.py,**/*.ts,**/*.tsx,**/*.js,**/*.svelte,**/*.sh,**/*.bash,**/*.fish,**/*.zsh,**/*.sql,**/*.yml,**/*.yaml,**/*.toml")
    p.add_argument("--binary-cutoff", type=int, default=256*1024)
    p.add_argument("--work", default=".git/tmp/heimgewebe-merge")
    return p.parse_args()

EXT_LANG = {
    ".rs":"Rust",".py":"Python",".ts":"TypeScript",".tsx":"TypeScript",".js":"JavaScript",
    ".svelte":"Svelte",".sh":"Shell",".bash":"Shell",".zsh":"Shell",".fish":"Shell",
    ".sql":"SQL",".yml":"YAML",".yaml":"YAML",".toml":"TOML",".md":"Markdown",
}

if __name__ == "__main__":
    a = parse_args()
    org = a.org
    repos = a.repos
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    work = Path(a.work)
    if work.exists(): shutil.rmtree(work)
    work.mkdir(parents=True, exist_ok=True)
    patterns = [p.strip() for p in a.globs.split(",") if p.strip()]

    # Parts
    parts: list[Path] = []
    cur_size = 0
    header = "# Heimgewebe – Gesamtüberblick (automatisch generiert)\n\n"
    parts, cur_size = append_with_split(out, parts, cur_size, a.max_bytes, header)

    # For index/crosslinks
    info_rows = []  # (repo, files, bytes, langs_dict)
    texts_by_repo: dict[str, list[tuple[str,str]]] = {}  # repo -> [(relpath, text), ...]

    # Helper: sichere Mermaid-IDs (alnum + _), Label separat
    def safe_id(name: str) -> str:
        return re.sub(r"[^A-Za-z0-9_]", "_", name)

    for repo in repos:
        repo_url = f"https://github.com/{org}/{repo}.git"
        repo_dir = work / repo
        print(f"• Cloning {repo_url}", file=sys.stderr)
        sh(["git","clone","--depth=1","--filter=blob:none", repo_url, str(repo_dir)])
        commit = sh(["git","rev-parse","HEAD"], cwd=repo_dir)
        files = sh(["git","ls-tree","-r","--name-only","HEAD"], cwd=repo_dir).splitlines()
        keep = [f for f in files if want(f, patterns)]

        repo_title = f"\n\n## {repo}@{commit[:12]}\n\n"
        parts, cur_size = append_with_split(out, parts, cur_size, a.max_bytes, repo_title)

        total_bytes = 0
        langs: dict[str,int] = {}
        texts: list[tuple[str,str]] = []

        for rel in keep:
            p = repo_dir / rel
            if not p.exists():
                try: sh(["git","checkout","--",rel], cwd=repo_dir)
                except subprocess.CalledProcessError: continue
            if not p.exists() or p.is_dir(): continue
            try:
                st = p.stat()
                total_bytes += st.st_size
                ext = p.suffix.lower()
                langs[EXT_LANG.get(ext, "Other")] = langs.get(EXT_LANG.get(ext,"Other"),0) + 1
                if st.st_size > a.binary_cutoff or looks_binary(p, a.binary_cutoff):
                    banner = f"\n<!-- skipped binary or large file: {rel} ({st.st_size} bytes) -->\n"
                    parts, cur_size = append_with_split(out, parts, cur_size, a.max_bytes, banner)
                    continue
                code = p.read_text(encoding="utf-8", errors="replace")
                texts.append((rel, code))
            except Exception:
                continue

        # write files content after collection for deterministic order
        for rel, code in texts:
            fence="```"
            banner = f"\n### {rel}\n\n{fence}\n{code}\n{fence}\n"
            parts, cur_size = append_with_split(out, parts, cur_size, a.max_bytes, banner)

        info_rows.append((repo, len(texts), total_bytes, langs))
        texts_by_repo[repo] = texts

    # Build index.md
    idx = out/"index.md"
    idx.write_text("## Index\n\n| Repo | Dateien | Größe | Sprachen (grobe Zählung) |\n|---|---:|---:|---|\n", encoding="utf-8")
    for (repo, cnt, b, langs) in info_rows:
        lang_str = ", ".join(f"{k}:{v}" for k,v in sorted(langs.items(), key=lambda x:(-x[1],x[0])) if v>0)
        idx.write_text(idx.read_text(encoding="utf-8")+f"| {repo} | {cnt} | {human_bytes(b)} | {lang_str} |\n", encoding="utf-8")

    # Cross-repo mentions (heuristic: wortgrenzen-suche, case-insensitiv)
    edges: dict[tuple[str,str], int] = {}
    for src in repos:
        texts = texts_by_repo.get(src, [])
        blob = "\n".join(t for _,t in texts)
        for dst in repos:
            if src==dst: continue
            # \b<dst>\b mit Escape (Repo-Namen können Bindestriche enthalten)
            pat = re.compile(rf'(?<!\w){re.escape(dst)}(?!\w)', re.IGNORECASE)
            n = len(pat.findall(blob))
            if n>0:
                edges[(src,dst)] = n

    # crosslinks.md
    cl = out/"crosslinks.md"
    cl.write_text("## Cross-Repo-Bezüge (Namens-Erwähnungen)\n\n", encoding="utf-8")
    if not edges:
        cl.write_text(cl.read_text(encoding="utf-8")+"*(keine Bezüge gefunden – Heuristik ist konservativ)*\n", encoding="utf-8")
    else:
        cl.write_text(cl.read_text(encoding="utf-8")+"Quelle: String-Suche nach Repo-Namen in Textdateien.\n\n", encoding="utf-8")
        cl.write_text(cl.read_text(encoding="utf-8")+"| Quelle → Ziel | Erwähnungen |\n|---|---:|\n", encoding="utf-8")
        for (s,d), n in sorted(edges.items(), key=lambda x:(x[0][0],x[0][1])):
            cl.write_text(cl.read_text(encoding="utf-8")+f"| {s} → {d} | {n} |\n", encoding="utf-8")

    # Mermaid
    mmd = out/"crosslinks.mmd"
    if not edges:
        mmd.write_text("graph LR\n  A[Keine Bezüge]--0-->B[—]\n", encoding="utf-8")
    else:
        lines = ["graph LR"]
        for (s,d), n in sorted(edges.items()):
            sid = safe_id(s)
            did = safe_id(d)
            # Node mit Label = Originalname
            lines.append(f'  {sid}["{s}"] -->|{n}| {did}["{d}"]')
        mmd.write_text("\n".join(lines)+"\n", encoding="utf-8")

    print("✓ merge completed", file=sys.stderr)
