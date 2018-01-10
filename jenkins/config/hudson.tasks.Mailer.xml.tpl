<?xml version='1.0' encoding='UTF-8'?>
<hudson.tasks.Mailer_-DescriptorImpl plugin="mailer@1.20">
  <defaultSuffix>@bazel.build</defaultSuffix>
  <hudsonUrl>https://ci.bazel.build/</hudsonUrl>
  <smtpAuthUsername>##SECRET:smtp.auth.username##</smtpAuthUsername>
  <smtpAuthPassword>##SECRET:smtp.auth.password##</smtpAuthPassword>
  <replyToAddress>bazel-ci@googlegroups.com</replyToAddress>
  <smtpHost>smtp.gmail.com</smtpHost>
  <useSsl>true</useSsl>
  <smtpPort>465</smtpPort>
  <charset>UTF-8</charset>
</hudson.tasks.Mailer_-DescriptorImpl>
