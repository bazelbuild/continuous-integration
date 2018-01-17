def job_lists(name, visibility):
  jobs = native.existing_rules()

  native.filegroup(
    name = name,
    srcs = [j for j in jobs if j.endswith("/all")],
    visibility = visibility,
  )
