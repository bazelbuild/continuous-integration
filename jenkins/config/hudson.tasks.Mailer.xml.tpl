<?xml version='1.0' encoding='UTF-8'?>
<hudson.tasks.Mailer_-DescriptorImpl plugin="mailer@1.15">
  <defaultSuffix>@google.com</defaultSuffix>
  <hudsonUrl>%{PUBLIC_JENKINS_URL}</hudsonUrl>
  <smtpAuthUsername>##SECRET:smtp.auth.username##</smtpAuthUsername>
  <smtpAuthPassword>##SECRET:smtp.auth.password##</smtpAuthPassword>
  <replyToAddress>bazel-ci@googlegroups.com</replyToAddress>
  <smtpHost>smtp.sendgrid.net</smtpHost>
  <useSsl>false</useSsl>
  <smtpPort>2525</smtpPort>
  <charset>UTF-8</charset>
</hudson.tasks.Mailer_-DescriptorImpl>
