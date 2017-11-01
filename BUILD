genrule(
    name = "git-hash",
    srcs = [".git/logs/HEAD"],
    outs = ["git-hash.txt"],
    cmd = "tail -1 $< | cut -d ' ' -f 2 > $@",
    visibility = ["//visibility:public"],
)
