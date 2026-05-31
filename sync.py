def sync_status_from_baidu() -> None:
    baidu_bin = resolve_path({"baidu": {"binary_path": "./bin/BaiduPCS-Go"}}, "baidu.binary_path")
    if not baidu_bin.exists():
        print("BaiduPCS-Go not found at", baidu_bin)
        return

    def parse_names(output):
        names = set()
        for line in output.split("\n"):
            parts = line.split()
            if len(parts) >= 5 and parts[0].isdigit():
                names.add(" ".join(parts[4:]).rstrip("/"))
        return names

    # Login
    bduss = os.environ.get("BDUSS", "")
    stoken = os.environ.get("STOKEN", "")
    if not bduss or not stoken:
        bduss_val = subprocess.run(["grep", "^export BDUSS=", str(Path.home()/".zshrc")], capture_output=True, text=True).stdout.strip().replace("export BDUSS=", "")
        stoken_val = subprocess.run(["grep", "^export STOKEN=", str(Path.home()/".zshrc")], capture_output=True, text=True).stdout.strip().replace("export STOKEN=", "")
        bduss = bduss or bduss_val
        stoken = stoken or stoken_val
    r = subprocess.run([str(baidu_bin), "login", f"-bduss={bduss}", f"-stoken={stoken}"], capture_output=True, text=True)
    if r.returncode != 0:
        print("Baidu login failed")
        return

    # Walk Baidu tree
    baidu_courses = set()
    for top_dir in parse_names(subprocess.run([str(baidu_bin), "ls", "/coursera"], capture_output=True, text=True).stdout):
        top_path = f"/coursera/{top_dir}"
        for cat in parse_names(subprocess.run([str(baidu_bin), "ls", top_path], capture_output=True, text=True).stdout):
            cat_path = f"{top_path}/{cat}"
            for course in parse_names(subprocess.run([str(baidu_bin), "ls", cat_path], capture_output=True, text=True).stdout):
                baidu_courses.add(course)

    courses = load_courses()
    status = load_status()
    fixed = 0
    for c in courses:
        name = c["name"]
        on_baidu = name in baidu_courses
        cur = status.get(c["slug"], {})
        if cur.get("downloaded") != on_baidu or cur.get("uploaded") != on_baidu:
            status.setdefault(c["slug"], {})["downloaded"] = on_baidu
            status.setdefault(c["slug"], {})["uploaded"] = on_baidu
            fixed += 1
            print(f"{'✅' if on_baidu else '⬜'} {c['slug']}")
    save_status(status)
    print(f"\nSynced {fixed} entries. {len(baidu_courses)} courses on Baidu.")