import streamlit as st
import zipfile
import os
import shutil
import re
import subprocess
import stat
import ast
import tempfile
from xml.etree import ElementTree as ET
from typing import Set, Tuple, List, Dict

TEMP_DIR = "temp"

def handle_remove_readonly(f, p, e):
    os.chmod(p, stat.S_IWRITE)
    f(p)

def clean_temp_folder():
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR, onerror=handle_remove_readonly)
    os.makedirs(TEMP_DIR)

def extract_zip(upf):
    clean_temp_folder()
    with zipfile.ZipFile(upf, 'r') as z:
        z.extractall(TEMP_DIR)

def clone_git_repo(git_url):
    clean_temp_folder()
    try:
        subprocess.run(["git", "clone", git_url, TEMP_DIR], check=True)
        return True
    except:
        return False

def checkout_pr_branch(pr):
    try:
        subprocess.run(["git", "-C", TEMP_DIR, "fetch", "origin"], check=True)
        subprocess.run(["git", "-C", TEMP_DIR, "fetch", "origin", f"pull/{pr}/head:pr-{pr}"], check=True)
        subprocess.run(["git", "-C", TEMP_DIR, "checkout", f"pr-{pr}"], check=True)
        return True
    except:
        return False

def find_coverage_report():
    for r, d, fs in os.walk(TEMP_DIR):
        if "coverage.xml" in fs:
            return os.path.join(r, "coverage.xml")
    return None

def parse_coverage_report(path):
    covered = set()
    tree = ET.parse(path)
    for cls in tree.findall(".//class"):
        fname = cls.attrib.get("filename")
        if fname:
            covered.add(os.path.normpath(fname))
    return covered

def identify_py_files() -> Tuple[Set[str], Set[str]]:
    src, tets = set(), set()
    for r, d, fs in os.walk(TEMP_DIR):
        for f in fs:
            if not f.endswith(".py"):
                continue
            fp, rel = os.path.join(r, f), os.path.relpath(os.path.join(r, f), TEMP_DIR)
            if re.match(r"(test_.*\.py|.*_test\.py)", f):
                tets.add(rel)
            else:
                src.add(rel)
    return src, tets

def get_functions(path):
    try:
        with open(path) as f:
            tree = ast.parse(f.read())
    except:
        return []
    return [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]

def match_tested_functions(srcs: Set[str], tests: Set[str]) -> Dict[str, Dict[str, List[str]]]:
    results = {}
    for s in srcs:
        funcs = get_functions(os.path.join(TEMP_DIR, s))
        tested, untested = [], []
        normed_src = {fn: re.sub(r'[_\-]', '', fn).lower() for fn in funcs}
        for fn, nfn in normed_src.items():
            found = False
            for t in tests:
                tfuns = get_functions(os.path.join(TEMP_DIR, t))
                for tf in tfuns:
                    if nfn in re.sub(r'[_\-]', '', tf).lower():
                        tested.append(fn)
                        found = True
                        break
                if found:
                    break
            if not found:
                untested.append(fn)
        results[s] = {"tested": tested, "untested": untested}
    return results

def get_default_branch():
    try:
        result = subprocess.run(
            ["git", "-C", TEMP_DIR, "symbolic-ref", "refs/remotes/origin/HEAD"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip().split("/")[-1]
    except:
        return "main"

def get_git_diff() -> List[str]:
    try:
        base_branch = get_default_branch()
        subprocess.run(["git", "-C", TEMP_DIR, "fetch", "origin"], check=True)
        subprocess.run(["git", "-C", TEMP_DIR, "checkout", base_branch], check=True)
        subprocess.run(["git", "-C", TEMP_DIR, "checkout", "-"], check=True)
        result = subprocess.run(
            ["git", "-C", TEMP_DIR, "diff", f"origin/{base_branch}..HEAD", "--name-only"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip().splitlines()
    except subprocess.CalledProcessError as e:
        return ["Couldn't generate diff:", e.stderr.strip()]

def llm_analysis(source_files: Set[str], test_files: Set[str]) -> str:
    lines = ["LLM-Based Coverage Analysis (Simulated):"]
    for src in source_files:
        if any(os.path.splitext(os.path.basename(src))[0] in test for test in test_files):
            lines.append(f"{src} appears to be tested based on file names.")
        else:
            lines.append(f"{src} seems untested.")
    return "\n".join(lines)

def ast_analysis(files: Set[str]) -> str:
    report = []
    for f in files:
        full_path = os.path.join(TEMP_DIR, f)
        try:
            with open(full_path, "r") as file:
                node = ast.parse(file.read())
                func_defs = [n.name for n in ast.walk(node) if isinstance(n, ast.FunctionDef)]
                report.append(f"{f} contains {len(func_defs)} function(s): {', '.join(func_defs)}")
        except Exception as e:
            report.append(f"Error parsing {f}: {str(e)}")
    return "\n".join(report)

st.title("Test and Coverage PR Analyzer")

mode = st.radio("Choose input method:", ("Upload ZIP file", "Enter Git Repo URL + PR"))

if mode == "Upload ZIP file":
    uploaded_file = st.file_uploader("Upload a zipped Python project", type=["zip"])
    if uploaded_file is not None:
        with st.spinner("Extracting and analyzing ZIP..."):
            extract_zip(uploaded_file)
            cov_path = find_coverage_report()
            if cov_path:
                st.success("Found coverage report")
                covered = parse_coverage_report(cov_path)
                st.write("Covered files:")
                st.code("\n".join(sorted(covered)))
            else:
                source_files, test_files = identify_py_files()
                st.subheader("LLM Test Insight")
                st.code(llm_analysis(source_files, test_files))
                st.subheader("AST Structure Review")
                st.code(ast_analysis(source_files))

                st.subheader("Function-level Coverage Analysis")
                func_map = match_tested_functions(source_files, test_files)
                for file, result in func_map.items():
                    st.markdown(f"**{file}**")
                    st.write("Tested functions:")
                    st.code("\n".join(result["tested"]) or "None")
                    st.write("Untested functions:")
                    st.code("\n".join(result["untested"]) or "None")
        clean_temp_folder()

elif mode == "Enter Git Repo URL + PR":
    git_url = st.text_input("Enter GitHub repo URL")
    pr_number = st.text_input("Enter PR number")
    if git_url and pr_number and st.button("Analyze PR"):
        with st.spinner("Cloning and analyzing PR..."):
            if not clone_git_repo(git_url):
                st.error("Failed to clone repo.")
            elif not checkout_pr_branch(pr_number):
                st.error("Failed to fetch/checkout PR.")
            else:
                source_files, test_files = identify_py_files()
                changed_files = get_git_diff()
                st.subheader("Files Changed in PR")
                st.code("\n".join(changed_files))

                changed_sources = {f for f in source_files if f in changed_files}

                st.subheader("LLM Test Insight (Changed Files)")
                st.code(llm_analysis(changed_sources, test_files))

                st.subheader("AST Review (Changed Files)")
                st.code(ast_analysis(changed_sources))

                st.subheader("Function-level Coverage Analysis (Changed Files)")
                func_map = match_tested_functions(changed_sources, test_files)
                for file, result in func_map.items():
                    st.markdown(f"**{file}**")
                    st.write("Tested functions:")
                    st.code("\n".join(result["tested"]) or "None")
                    st.write("Untested functions:")
                    st.code("\n".join(result["untested"]) or "None")
        clean_temp_folder()
