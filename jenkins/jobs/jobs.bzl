def _is_testing(job):
  # We include all test but the docker ones (because they need access to the
  # Docker server).
  return not "docker" in job and job != "continuous-integration"

def job_lists(name = "jobs", visibility = None):
  jobs = native.existing_rules()

  native.filegroup(
    name = name,
    srcs = [j for j in jobs if j.endswith("/all")],
    visibility = visibility,
  )

  native.filegroup(
    name = "test-" + name,
    srcs = [j for j in jobs if j.endswith("/test") and _is_testing(j[:-5])],
    visibility = visibility,
  )
