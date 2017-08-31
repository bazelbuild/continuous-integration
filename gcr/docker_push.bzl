# Copyright 2016 The Bazel Authors. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Quick and not really nice docker_push rules based on the docker daemon."""

def _get_runfile_path(ctx, f):
  """Return the runfiles relative path of f."""
  if ctx.workspace_name:
    return ctx.workspace_name + "/" + f.short_path
  else:
    return f.short_path

def _reverse(lst):
  result = []
  for el in lst:
    result = [el] + result
  return result

def _generate_load_statement(ctx, tag, file):
  return ("echo 'Image %s'\n" % tag) + "\n".join([
      "incr_load '%s' '%s'" %  (_get_runfile_path(ctx, l["id"]),
                                _get_runfile_path(ctx, l["layer"]))
      for l in _reverse(file.docker_layers)
  ]) + ("\ntag_last_load '%s'" % tag)

# TODO(dmarting): replace with proper docker_push using the docker library.
def _impl(ctx):
  files = dict()
  for i in range(len(ctx.attr.image_tags)):
    tag = ctx.attr.image_tags[i]
    file = ctx.attr.images[i]
    files[tag] = file

  ctx.template_action(
      template = ctx.file._template,
      substitutions = {
          "%{load_statements}": "\n\n".join(
              [_generate_load_statement(ctx, tag, files[tag]) for tag in ctx.attr.image_tags]),
          "%{repository}": ctx.attr.repository,
          "%{tags}": " ".join(ctx.attr.image_tags)
      },
      output = ctx.outputs.executable,
      executable = True,
  )
  runfiles = []
  for s in ctx.attr.images:
    for l in s.docker_layers:
      runfiles.append(l["layer"])
      runfiles.append(l["id"])

  return struct(runfiles = ctx.runfiles(files = runfiles))

_docker_push = rule(
    implementation = _impl,
    attrs = {
        "repository": attr.string(mandatory=True),
        "_template": attr.label(
            default=Label("//gcr:docker_push_template.sh.tpl"),
            single_file=True,
            allow_files=True),
        "image_tags": attr.string_list(),
        "images": attr.label_list(providers=["docker_layers"]),
    },
    executable = True,
)

def docker_push(images, **kwargs):
  _docker_push(
      images = [k for k in images],
      image_tags = [images[k] for k in images],
      **kwargs
  )
